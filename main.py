import streamlit as st
import datetime
import time
import datetime
import streamlit.components.v1 as components
from datetime import datetime,timedelta;
import pandas as pd
import streamlit.components.v1 as components
import database as db

# 初始化
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'tasks' not in st.session_state:
    st.session_state.tasks = []
if 'editing_task' not in st.session_state:
    st.session_state.editing_task = None

# 页面配置
st.set_page_config(
    page_title="个人效率工具",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def show_auth():
    """显示认证界面"""
    tab1, tab2 = st.tabs(["登录", "注册"])
    
    with tab1:
        with st.form("登录表单"):
            st.subheader("用户登录")
            login_username = st.text_input("用户名", key="login_username")
            login_password = st.text_input("密码", type="password", key="login_password")
            login_submit = st.form_submit_button("登录")
            
            if login_submit:
                user_id = db.verify_user(login_username, login_password)
                if user_id:
                    st.session_state.user_id = user_id
                    st.session_state.username = login_username
                    st.session_state.tasks = db.get_user_tasks(user_id)
                    st.success(f"欢迎回来，{login_username}！")
                    st.rerun()
                else:
                    st.error("用户名或密码错误")
    
    with tab2:
        with st.form("注册表单"):
            st.subheader("用户注册")
            reg_username = st.text_input("用户名", key="reg_username")
            reg_password = st.text_input("密码", type="password", key="reg_password")
            reg_confirm = st.text_input("确认密码", type="password", key="reg_confirm")
            reg_submit = st.form_submit_button("注册")
            
            if reg_submit:
                if reg_password != reg_confirm:
                    st.error("两次输入的密码不一致")
                elif len(reg_username) < 3:
                    st.error("用户名至少需要3个字符")
                elif len(reg_password) < 6:
                    st.error("密码至少需要6个字符")
                else:
                    if db.create_user(reg_username, reg_password):
                        st.success("注册成功！请登录")
                    else:
                        st.error("用户名已存在")

# 未登录，显示登录界面
if st.session_state.user_id is None:
    st.title("个人效率工具")
    show_auth()
    st.stop()


with st.sidebar:
    st.markdown(f"# 🚀 个人效率工具")
    st.markdown(f"**欢迎，{st.session_state.username}**")
    st.markdown("---")
    
    page = st.radio(
        "选择功能",
        ["主页", "📚 日程记录", "📅 甘特图"],
        index=0
    )
    
    st.markdown("---")
    if st.button("退出登录"):
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.tasks = []
        st.rerun()
    
    st.info("选择左侧功能来管理你的时间和任务")

if "甘特图" in page:
    st.title("📅 甘特图")
    
    # 初始化
    if 'gantt_tasks' not in st.session_state:
        # 检查标记任务
        try:
            expired_tasks = db.check_and_mark_expired_tasks(st.session_state.user_id)
            if expired_tasks:
                st.info(f"自动标记了 {len(expired_tasks)} 个过期任务为完成")
        except Exception as e:
            st.error(f"检查过期任务时出错: {e}")
        
        st.session_state.gantt_tasks = db.get_incomplete_tasks(st.session_state.user_id)
    
    if 'completed_tasks' not in st.session_state:
        st.session_state.completed_tasks = db.get_completed_tasks(st.session_state.user_id)
    
    if 'editing_gantt_task' not in st.session_state:
        st.session_state.editing_gantt_task = None
    
    if 'scoring_task' not in st.session_state:
        st.session_state.scoring_task = None
    
    # 检查
    unscored_tasks = db.get_unscored_completed_tasks(st.session_state.user_id)
    if unscored_tasks and 'showing_score_dialog' not in st.session_state:
        st.session_state.showing_score_dialog = True
        st.session_state.scoring_task = unscored_tasks[0] 
    
    # 评分
    if st.session_state.scoring_task:
        task_id, title, start_date, end_date = st.session_state.scoring_task
        with st.form("任务评分表单", clear_on_submit=True):
            st.subheader(f"为任务评分: {title}")
            st.write(f"任务时间: {start_date} 至 {end_date}")
            
            score = st.slider("请为这个任务完成情况评分", 1, 5, 3, 
                            help="1分: 很不满意, 5分: 非常满意")
            
            col1, col2 = st.columns(2)
            with col1:
                submit_score = st.form_submit_button("提交评分")
            with col2:
                skip_score = st.form_submit_button("稍后评分")
            
            if submit_score:
                db.mark_task_completed(task_id, score)
                st.success("评分已提交！")
                # 更新
                st.session_state.gantt_tasks = db.get_incomplete_tasks(st.session_state.user_id)
                st.session_state.completed_tasks = db.get_completed_tasks(st.session_state.user_id)
                st.session_state.scoring_task = None
                st.session_state.showing_score_dialog = False
                st.rerun()
            
            if skip_score:
                st.session_state.scoring_task = None
                st.session_state.showing_score_dialog = False
                st.rerun()
    # 添加
    if "show_gantt_form" not in st.session_state:
        st.session_state.show_gantt_form = False
    
    if st.button("➕ 添加新任务"):
        st.session_state.show_gantt_form = True
        st.session_state.editing_gantt_task = None
    
    if st.session_state.show_gantt_form:
        with st.form("甘特图任务表单", clear_on_submit=True):
            st.subheader("添加新任务" if st.session_state.editing_gantt_task is None else "编辑任务")
            
            title = st.text_input("任务名称", 
                                value=st.session_state.get('gantt_edit_title', ''))
            description = st.text_area("任务描述", 
                                     value=st.session_state.get('gantt_edit_description', ''))
            
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("开始日期", 
                                         value=st.session_state.get('gantt_edit_start_date', datetime.now().date()))
            with col2:
                end_date = st.date_input("结束日期", 
                                       value=st.session_state.get('gantt_edit_end_date', datetime.now().date() + timedelta(days=1)))
            
            color_options = {
                "红色": "#FF6B6B",
                "蓝色": "#45B7D1", 
                "绿色": "#96CEB4",
                "黄色": "#FFEAA7",
                "紫色": "#DDA0DD",
                "青色": "#4ECDC4"
            }
            selected_color = st.selectbox("任务颜色", list(color_options.keys()),
                                        index=list(color_options.keys()).index(st.session_state.get('gantt_edit_color_name', "蓝色")))
            
            progress = st.slider("进度 (%)", 0, 100, 
                               value=st.session_state.get('gantt_edit_progress', 0))
            
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("保存任务")
            with col2:
                cancel = st.form_submit_button("取消")
            
            if submit and title:
                # 日期限制
                if end_date < start_date:
                    st.error("结束日期不能早于开始日期")
                else:
                    color = color_options[selected_color]
                    
                    if st.session_state.editing_gantt_task is None:
                        # 新增
                        task_id = db.add_gantt_task(st.session_state.user_id, title, description, 
                                                  start_date.strftime("%Y-%m-%d"), 
                                                  end_date.strftime("%Y-%m-%d"),
                                                  color, progress)
                        st.success("任务添加成功！")
                    else:
                        # 编辑
                        db.update_gantt_task(st.session_state.editing_gantt_task, title, description,
                                           start_date.strftime("%Y-%m-%d"), 
                                           end_date.strftime("%Y-%m-%d"),
                                           color, progress)
                        st.success("任务更新成功！")
                    
                    # 更新
                    st.session_state.gantt_tasks = db.get_incomplete_tasks(st.session_state.user_id)
                    st.session_state.completed_tasks = db.get_completed_tasks(st.session_state.user_id)
                    st.session_state.show_gantt_form = False
                    st.session_state.editing_gantt_task = None

                    for key in ['gantt_edit_title', 'gantt_edit_description', 'gantt_edit_start_date', 
                               'gantt_edit_end_date', 'gantt_edit_color_name', 'gantt_edit_progress']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
            
            if cancel:
                st.session_state.show_gantt_form = False
                st.session_state.editing_gantt_task = None
                
                for key in ['gantt_edit_title', 'gantt_edit_description', 'gantt_edit_start_date', 
                           'gantt_edit_end_date', 'gantt_edit_color_name', 'gantt_edit_progress']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
    
    # 显示
    if st.session_state.gantt_tasks:
        
        all_dates = []
        for task in st.session_state.gantt_tasks:
            task_id, title, description, start_date, end_date, color, progress, score = task
            all_dates.append(datetime.strptime(start_date, "%Y-%m-%d").date())
            all_dates.append(datetime.strptime(end_date, "%Y-%m-%d").date())
        
        if all_dates:
            min_date = min(all_dates)
            max_date = max(all_dates)
            
            # 生成日期范围
            date_range = []
            current_date = min_date
            while current_date <= max_date:
                date_range.append(current_date)
                current_date += timedelta(days=1)
            
            # 过滤
            today = datetime.now().date()
            filtered_dates = [date for date in date_range if date >= today]

            if not filtered_dates:
                filtered_dates = [today]
            
            date_columns = [date.strftime("%m/%d")  for date in filtered_dates]
            gantt_df = pd.DataFrame(index=[task[1] for task in st.session_state.gantt_tasks], 
                                columns=date_columns)
            
            # 填充
            for task in st.session_state.gantt_tasks:
                task_id, title, description, start_date, end_date, color, progress, score = task
                start = datetime.strptime(start_date, "%Y-%m-%d").date()
                end = datetime.strptime(end_date, "%Y-%m-%d").date()
                
                # 标记任务期间的日期
                current = start
                while current <= end:
                    if current >= today:
                        date_str = current.strftime("%m/%d")
                        if date_str in date_columns:
                            # 使用特殊标记表示任务期间
                            gantt_df.loc[title, date_str] = "task"
                    current += timedelta(days=1)
            
            # 创建表格
            def gantt_to_html(df, tasks):
                html = ['<div style="overflow-x: auto;">']
                html.append('<table style="border-collapse: collapse; width: 100%; table-layout: fixed; font-size: 12px;">')
                
                html.append('<tr>')
                html.append('<th style="border: 1px solid #ddd; padding: 8px; background-color: #f2f2f2; width: 150px; text-align: center;">任务</th>')
                html.append('<th style="border: 1px solid #ddd; padding: 8px; background-color: #f2f2f2; width: 100px; text-align: center;">倒计时</th>')
                for col in df.columns:
                    html.append(f'<th style="border: 1px solid #ddd; padding: 8px; background-color: #f2f2f2; width: 40px; text-align: center;">{col}</th>')
                html.append('</tr>')
                
                today = datetime.now().date()
                for idx, row in df.iterrows():
                    html.append('<tr style="height: 40px;">')
                    
                    current_task = None
                    for task in tasks:
                        if task[1] == idx:
                            current_task = task
                            break
                    
                    if current_task:
                        task_id, title, description, start_date, end_date, color, progress, score = current_task
                        start = datetime.strptime(start_date, "%Y-%m-%d").date()
                        end = datetime.strptime(end_date, "%Y-%m-%d").date()
                        
                        html.append(f'<td style="border: 1px solid #ddd; padding: 4px; background-color: #f8f9fa; text-align: left; vertical-align: middle;"><strong>{title}</strong></td>')
                        
                        # 倒计时
                        countdown_text = ""
                        
                        if today < start:
                            # 未开始 - 开始倒计时
                            days_until_start = (start - today).days
                            if days_until_start <= 1:
                                countdown_text = f"<span style='color: red; font-weight: bold;'>即将开始: {days_until_start}天</span>"
                            else:
                                countdown_text = f"开始: {days_until_start}天"
                        elif today <= end:
                            # 进行中 - 显示结束倒计时
                            days_until_end = (end - today).days
                            if days_until_end <= 1:
                                countdown_text = f"<span style='color: red; font-weight: bold;'>即将结束: {days_until_end}天</span>"
                            else:
                                countdown_text = f"结束: {days_until_end}天"
                        else:
                            # 已结束
                            countdown_text = "<span style='color: orange; font-weight: bold;'>已过期</span>"
                        
                        html.append(f'<td style="border: 1px solid #ddd; padding: 4px; background-color: #f8f9fa; text-align: center; vertical-align: middle;">{countdown_text}</td>')
                        
                        for cell in row:
                            if pd.notna(cell) and cell == "task":
                                html.append(f'<td style="border: 1px solid #ddd; padding: 0; background-color: {color}; text-align: center; vertical-align: middle;"></td>')
                            else:
                                html.append('<td style="border: 1px solid #ddd; padding: 0; text-align: center; vertical-align: middle;"></td>')
                    html.append('</tr>')
                
                html.append('</table>')
                html.append('</div>')
                return ''.join(html)
            
            # 显示甘特图
            st.markdown("### 项目甘特图")
            components.html(gantt_to_html(gantt_df.fillna(""), st.session_state.gantt_tasks), 
                        height=min(600, 40 * len(st.session_state.gantt_tasks) + 100), 
                        scrolling=True)

        # 任务管理
        st.markdown("### 任务管理")

        st.markdown("""
        <style>
        .incomplete-task .stProgress > div > div {
            width: 80% !important;
        }
        </style>
        """, unsafe_allow_html=True)

        for task in st.session_state.gantt_tasks:
            task_id, title, description, start_date, end_date, color, progress, score = task
            
            today = datetime.now().date()
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
            
            # 进度
            if today < start:
                auto_progress = 0
                countdown_text = f"开始: {(start - today).days}天"
                if (start - today).days <= 1:
                    countdown_text = f"<span style='color: red; font-weight: bold;'>即将开始: {(start - today).days}天</span>"
            elif today > end:
                # 任务已过期
                auto_progress = 100
                countdown_text = "<span style='color: orange; font-weight: bold;'>已过期</span>"
            else:
                # 进行中
                total_days = (end - start).days
                elapsed_days = (today - start).days
                if total_days > 0:
                    auto_progress = min(100, int((elapsed_days / total_days) * 100))
                else:
                    auto_progress = 100 
                    
                countdown_text = f"结束: {(end - today).days}天"
                if (end - today).days <= 1:
                    countdown_text = f"<span style='color: red; font-weight: bold;'>即将结束: {(end - today).days}天</span>"
            
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
            with col1:
                st.write(f"**{title}** - {start_date} 至 {end_date}")
                st.markdown(countdown_text, unsafe_allow_html=True)
                st.markdown('<div class="incomplete-task">', unsafe_allow_html=True)
                st.progress(auto_progress/100)
                st.markdown('</div>', unsafe_allow_html=True)
                if description:
                    st.caption(description)
            with col2:
                st.write(f"进度: {auto_progress}%")
            with col3:
                if st.button("标记完成", key=f"complete_{task_id}"):
                    st.session_state.scoring_task = (task_id, title, start_date, end_date)
                    st.rerun()
            with col4:
                if st.button("编辑", key=f"gantt_edit_{task_id}"):
                    st.session_state.editing_gantt_task = task_id
                    st.session_state.gantt_edit_title = title
                    st.session_state.gantt_edit_description = description
                    st.session_state.gantt_edit_start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
                    st.session_state.gantt_edit_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
                    
                    color_names = {
                        "#FF6B6B": "红色",
                        "#45B7D1": "蓝色", 
                        "#96CEB4": "绿色",
                        "#FFEAA7": "黄色",
                        "#DDA0DD": "紫色",
                        "#4ECDC4": "青色"
                    }
                    st.session_state.gantt_edit_color_name = color_names.get(color, "蓝色")
                    st.session_state.gantt_edit_progress = auto_progress 
                    st.session_state.show_gantt_form = True
                    st.rerun()
            with col5:
                if st.button("删除", key=f"gantt_delete_{task_id}"):
                    db.delete_gantt_task(task_id)
                    st.session_state.gantt_tasks = db.get_incomplete_tasks(st.session_state.user_id)
                    st.session_state.completed_tasks = db.get_completed_tasks(st.session_state.user_id)
                    st.success("任务已删除")
                    st.rerun()
    else:
            st.info("还没有添加任何未完成的甘特图任务")
    
    # 已完成任务
    if st.session_state.completed_tasks:
        st.markdown("---")
        with st.expander(f"📁 已完成的任务 ({len(st.session_state.completed_tasks)}个)", expanded=False):
            st.markdown("### 已完成的任务")
            
            tasks_to_delete = []
            
            for task in st.session_state.completed_tasks:
                task_id, title, start_date, end_date, score, completed_at = task
                
                # 格式化
                completed_time = ""
                if completed_at:
                    try:
                        completed_dt = datetime.strptime(completed_at, "%Y-%m-%d %H:%M:%S")
                        completed_time = completed_dt.strftime("%m/%d %H:%M")
                    except:
                        completed_time = completed_at
                
                # 显示评分
                score_stars = "⭐" * (score if score else 0)
                
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{title}** - {start_date} 至 {end_date}")
                    if completed_time:
                        st.caption(f"完成于: {completed_time}")
                with col2:
                    if score:
                        st.write(f"评分: {score_stars}")
                    else:
                        st.write("未评分")
                with col3:
                    delete_key = f"delete_completed_{task_id}"
                    if delete_key not in st.session_state:
                        st.session_state[delete_key] = False
                    
                    if not st.session_state[delete_key]:
                        # 第一次点击
                        if st.button("删除", key=f"init_delete_{task_id}"):
                            st.session_state[delete_key] = True
                            st.rerun()
                    else:
                        # 第二次点击
                        st.warning("确认删除此任务？")
                        col_confirm, col_cancel = st.columns(2)
                        with col_confirm:
                            if st.button("确认删除", key=f"confirm_delete_{task_id}", type="primary"):
                                tasks_to_delete.append(task_id)
                        with col_cancel:
                            if st.button("取消", key=f"cancel_delete_{task_id}"):
                                st.session_state[delete_key] = False
                                st.rerun()
            
            if tasks_to_delete:
                for task_id in tasks_to_delete:
                    db.delete_gantt_task(task_id)
                    delete_key = f"delete_completed_{task_id}"
                    if delete_key in st.session_state:
                        del st.session_state[delete_key]
                
                # 更新
                st.session_state.completed_tasks = db.get_completed_tasks(st.session_state.user_id)
                st.success(f"已删除 {len(tasks_to_delete)} 个任务")
                st.rerun()
    else:
        st.info("还没有已完成的任务")


elif "主页" in page:
    st.title("这是一个主页")
    
    likes_count = db.get_likes_count()
    
    intro, why, thanks = st.tabs(["**介绍**", "**为何**", "**感谢**"])
    
    with intro:
        st.markdown("""
        这是一个专为帮助您更好地管理时间和任务而设计的应用程序，提供了形象化的任务管理服务
        
        ## 主要功能
        
        - 📚 **日程记录** - 详细的日程记录和时间管理
        - 📅 **甘特图** - 项目进度可视化和任务跟踪
        - 仍在开发
        
        ## 详细介绍
        
        **日程记录：**
                    
        像课表一样明确看到的日程安排，用大小直观地展示时间
                    
        **甘特图：**
                    
        甘特图以图示通过活动列表和时间刻度表示出特定项目的顺序与持续时间。一条线条图，横轴表示时间，纵轴表示项目，线条表示期间计划和实际完成情况。直观表明计划何时进行，进展与要求的对比。便于管理者弄清项目的剩余任务，评估工作进度。
        """)
        
       
    
    with why:
        st.markdown("""
        ### 为什么我要做这个网站？
        
        > 你 是 否 也 被 繁 杂 事 务 烦 扰？  
        > 看 着 一 条 条 待 办 事 项  
        > 是 否 仍 然 无 从 下 手？  
        > “ 数 缺 形 时 少 直 观”  
        > 让 形 象 化 的 时 间 管 理 网 站 来 帮 助 你 吧
        
        ### 初衷
        
        这个项目源于个人对高效时间管理的需求。市面上的时间管理工具要么功能过于复杂，
        要么需要付费订阅。我希望创建一个简单、直观且免费的工具，帮助大家更好地规划时间。
        
        ### 愿景
        
        希望通过这个工具，能够让更多人享受到高效时间管理带来的便利，
        让每一天都过得更加充实和有意义。
        """)
    
    
    with thanks:
        st.markdown("""
        ## 感谢
        
        ### 感谢使用
        
        衷心感谢每一位使用这个工具的用户！您的支持是我们持续改进的动力。
        
        ### 特别鸣谢
        
        - 感谢老师和助教的大力支持
        - 感谢deepseek，协助我完成了一些代码
        - 感谢我自己
        - 感谢streamlit提供的平台
        """)
        
        st.markdown("---")
        st.markdown("### 喜欢这个工具吗？")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button(f"❤️ 点赞 ({likes_count})", use_container_width=True, type="primary"):
                new_count = db.increment_likes()
                st.success(f"感谢您的点赞！总点赞数: {new_count}")
                st.balloons()  
                st.rerun()
        with col2:
            if st.button(f"支持这个网站 ", use_container_width=True, type="primary"):
                st.markdown("感谢支持，不必V我50")

    

elif "日程记录" in page:
    st.title("📚 日程记录")
    
    # 日期范围选择
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        start_date = st.date_input("开始日期", value=datetime.now().date())
    with col2:
        end_date = st.date_input("结束日期", value=datetime.now().date() + timedelta(days=6))
    with col3:
        st.write("")  # 占位
        if st.button("今天"):
            start_date = datetime.now().date()
            end_date = start_date + timedelta(days=6)
            st.rerun()
    
    # 日期限制
    if end_date < start_date:
        st.error("结束日期不能早于开始日期")
        end_date = start_date
    
    # 生成日期
    date_range = []
    current_date = start_date
    while current_date <= end_date:
        date_range.append(current_date)
        current_date += timedelta(days=1)
    
    # 生成时间选项
    def generate_time_slots():
        time_slots = []
        for hour in range(5, 24):
            for minute in [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]:
                time_slots.append(f"{hour:02d}:{minute:02d}")
        time_slots.append("24:00")
        return time_slots
    
    time_slots = generate_time_slots()
    
    # 时间标签（20分钟一次）
    def generate_display_time_slots():
        display_slots = []
        for hour in range(5, 24):
            for minute in [0, 20, 40]:
                display_slots.append(f"{hour:02d}:{minute:02d}")
        display_slots.append("24:00")
        return display_slots
    
    display_time_slots = generate_display_time_slots()
    

    date_columns = [date.strftime("%m/%d") + f"({['一','二','三','四','五','六','日'][date.weekday()]})" for date in date_range]
    schedule_df = pd.DataFrame(index=display_time_slots, columns=date_columns)
    
    # 添加任务对话框
    if "show_task_form" not in st.session_state:
        st.session_state.show_task_form = False
    
    if st.button("➕ 添加新任务"):
        st.session_state.show_task_form = True
        st.session_state.editing_task = None
    
    if st.session_state.show_task_form:
        with st.form("任务表单", clear_on_submit=True):
            st.subheader("添加新任务" if st.session_state.editing_task is None else "编辑任务")
            
            title = st.text_input("任务标题", 
                                value=st.session_state.get('edit_title', ''))
            description = st.text_area("任务描述", 
                                     value=st.session_state.get('edit_description', ''))
            
            col1, col2 = st.columns(2)
            with col1:
                task_date = st.date_input("任务日期", 
                                        value=st.session_state.get('edit_date', datetime.now().date()))
            
            with col2:
                st.write("开始时间")
                col_start_hour, col_start_min = st.columns(2)
                with col_start_hour:
                    start_hour = st.selectbox("小时", range(5, 24), 
                                            index=st.session_state.get('edit_start_hour', 0),
                                            key="start_hour")
                with col_start_min:
                    start_min = st.selectbox("分钟", [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55],
                                           index=st.session_state.get('edit_start_min', 0),
                                           key="start_min")
                
                st.write("结束时间")
                col_end_hour, col_end_min = st.columns(2)
                with col_end_hour:
                    end_hour = st.selectbox("小时", range(5, 25),  # 包含24
                                          index=st.session_state.get('edit_end_hour', 1),
                                          key="end_hour")
                with col_end_min:
                    end_min = st.selectbox("分钟", [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55],
                                         index=st.session_state.get('edit_end_min', 0),
                                         key="end_min")
            
            # 组合时间
            start_slot = f"{start_hour:02d}:{start_min:02d}"
            end_slot = f"{end_hour:02d}:{end_min:02d}"
            
            # 验证
            if start_slot >= end_slot:
                st.error("结束时间必须晚于开始时间")
            
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("保存任务")
            with col2:
                cancel = st.form_submit_button("取消")
            
            if submit and title and start_slot < end_slot:
                # 保存
                task_date_str = task_date.strftime("%Y-%m-%d")
                
                if st.session_state.editing_task is None:
                    # 新增
                    task_id = db.add_task(st.session_state.user_id, title, description, 
                                                  task_date_str, start_slot, end_slot)
                    st.success("任务添加成功！")
                else:
                    # 编辑
                    db.update_task(st.session_state.editing_task, title, description,
                                           task_date_str, start_slot, end_slot)
                    st.success("任务更新成功！")
                
                # 更新
                st.session_state.tasks = db.get_user_tasks_by_date_range(
                    st.session_state.user_id, 
                    start_date.strftime("%Y-%m-%d"),
                    end_date.strftime("%Y-%m-%d")
                )
                st.session_state.show_task_form = False
                st.session_state.editing_task = None
                
                for key in ['edit_title', 'edit_description', 'edit_date', 
                           'edit_start_hour', 'edit_start_min', 'edit_end_hour', 'edit_end_min']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
            
            if cancel:
                st.session_state.show_task_form = False
                st.session_state.editing_task = None
                for key in ['edit_title', 'edit_description', 'edit_date', 
                           'edit_start_hour', 'edit_start_min', 'edit_end_hour', 'edit_end_min']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
    
    # 显示
    st.markdown(f"### {start_date.strftime('%Y/%m/%d')} - {end_date.strftime('%Y/%m/%d')} 日程记录")
    
    # 获取任务
    current_tasks = db.get_user_tasks_by_date_range(
        st.session_state.user_id, 
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d")
    )
    
    # 创建表格
    def style_schedule(df, tasks, date_columns):
        """为表格添加样式"""
        styled_df = df.copy()
        
        predefined_colors = [
            "#FF9AA2",  
            "#FFB7B2",  
            "#FFDAC1",  
            "#E2F0CB", 
            "#B5EAD7",  
            "#D3B5E7",  
            "#64C8F0FD",  
            "#F8B195",  
            "#F67280",  
            "#D67993",  
            "#A764E2AC",  
            "#2583D6A9",  
        ]
        
        task_colors = {}
        for i, task in enumerate(tasks):
            task_id, title, description, task_date, start, end = task
            if task_id not in task_colors:
                color_index = task_id % len(predefined_colors)
                task_colors[task_id] = predefined_colors[color_index]
        
        color_df = pd.DataFrame(index=display_time_slots, columns=date_columns)
        
        for task in tasks:
            task_id, title, description, task_date, start, end = task
            color = task_colors[task_id]
            
            # 显示
            task_date_obj = datetime.strptime(task_date, "%Y-%m-%d").date()
            date_str = task_date_obj.strftime("%m/%d") + f"({['一','二','三','四','五','六','日'][task_date_obj.weekday()]})"
            
            if date_str in date_columns:
                col_idx = date_columns.index(date_str)
                
                try:
                    start_idx = time_slots.index(start)
                    end_idx = time_slots.index(end)
                    
                    display_start_idx = start_idx // 4  
                    display_end_idx = (end_idx - 1) // 4 + 1 
                    
                    for i in range(display_start_idx, min(display_end_idx, len(display_time_slots))):
                        current_value = styled_df.iat[i, col_idx]
                        new_value = f"{title}" if pd.isna(current_value) or current_value == "" else f"{current_value}<br>{title}"
                        styled_df.iat[i, col_idx] = new_value
                        
                        color_df.iat[i, col_idx] = color
                except ValueError:
                    continue
        
        return styled_df, color_df
    
    if current_tasks:
        styled_schedule, color_schedule = style_schedule(schedule_df, current_tasks, date_columns)
        
        def dataframe_to_html(df, color_df):
            html = ['<div style="overflow-x: auto;">']
            html.append('<table style="border-collapse: collapse; width: 100%; table-layout: fixed; font-size: 12px;">')
            
            # 表头
            html.append('<tr>')
            html.append('<th style="border: 1px solid #ddd; padding: 4px; background-color: #f2f2f2; width: 80px; text-align: center;">时间</th>')
            for col in df.columns:
                html.append(f'<th style="border: 1px solid #ddd; padding: 4px; background-color: #f2f2f2; width: 120px; text-align: center;">{col}</th>')
            html.append('</tr>')
            
            #内容
            for idx, row in df.iterrows():
                html.append('<tr style="height: 30px;">') 
                html.append(f'<td style="border: 1px solid #ddd; padding: 2px; background-color: #f8f9fa; text-align: center; vertical-align: middle;"><strong>{idx}</strong></td>')
                
                for j, cell in enumerate(row):
                    cell_color = color_df.iat[df.index.get_loc(idx), j] if not pd.isna(color_df.iat[df.index.get_loc(idx), j]) else ""
                    
                    if pd.notna(cell) and cell != "":
                        # 多任务检测
                        tasks_in_cell = str(cell).split('<br>')
                        if len(tasks_in_cell) > 1:
                            # 如果任务太多，只显示前2个，其余用"..."表示
                            if len(tasks_in_cell) > 2:
                                display_tasks = tasks_in_cell[:2]
                                display_tasks.append("...")
                            else:
                                display_tasks = tasks_in_cell
                            cell_content = "<br>".join([f"• {task}" for task in display_tasks])
                            html.append(f'<td style="border: 1px solid #ddd; padding: 2px; background-color: {cell_color}; text-align: left; vertical-align: top; overflow: hidden; word-wrap: break-word;">{cell_content}</td>')
                        else:
                            html.append(f'<td style="border: 1px solid #ddd; padding: 2px; background-color: {cell_color}; text-align: left; vertical-align: middle; overflow: hidden; word-wrap: break-word;">• {cell}</td>')
                    else:
                        html.append(f'<td style="border: 1px solid #ddd; padding: 2px; text-align: center; vertical-align: middle; background-color: {cell_color};"></td>')
                html.append('</tr>')
            
            html.append('</table>')
            html.append('</div>')
            return ''.join(html)
        
        # 显示表格
        components.html(dataframe_to_html(styled_schedule, color_schedule), height=800, scrolling=True)
        
        # 任务管理
        st.markdown("### 任务管理")
        for task in current_tasks:
            task_id, title, description, task_date, start, end = task
            
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                task_date_obj = datetime.strptime(task_date, "%Y-%m-%d").date()
                date_display = task_date_obj.strftime("%Y年%m月%d日") + f"({['一','二','三','四','五','六','日'][task_date_obj.weekday()]})"
                st.write(f"**{title}** - {date_display} {start}-{end}")
                if description:
                    st.caption(description)
            with col2:
                if st.button("编辑", key=f"edit_{task_id}"):
                    st.session_state.editing_task = task_id
                    st.session_state.edit_title = title
                    st.session_state.edit_description = description
                    st.session_state.edit_date = datetime.strptime(task_date, "%Y-%m-%d").date()
                    
                    # 解析开始时间和结束时间
                    start_hour, start_min = map(int, start.split(':'))
                    end_hour, end_min = map(int, end.split(':'))
                    
                    st.session_state.edit_start_hour = start_hour - 5  
                    st.session_state.edit_start_min = start_min // 5  
                    st.session_state.edit_end_hour = end_hour - 5      
                    st.session_state.edit_end_min = end_min // 5       
                    
                    st.session_state.show_task_form = True
                    st.rerun()
            with col3:
                if st.button("删除", key=f"delete_{task_id}"):
                    db.delete_task(task_id)
                    # 重新获取当前日期范围内的任务
                    current_tasks = db.get_user_tasks_by_date_range(
                        st.session_state.user_id, 
                        start_date.strftime("%Y-%m-%d"),
                        end_date.strftime("%Y-%m-%d")
                    )
                    st.success("任务已删除")
                    st.rerun()
    else:
        st.info("在选定日期范围内还没有添加任何任务，点击上方的「添加新任务」按钮开始规划吧！")    