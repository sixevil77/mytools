import streamlit as st
import plotly.express as px
import random

import pandas as pd

import requests
import json
import time
import html

from datetime import datetime, timezone, timedelta, date
from tinydb import TinyDB, Query, JSONStorage
from tinydb_serialization import SerializationMiddleware
from tinydb_serialization.serializers import DateTimeSerializer

import openai
openai.api_base="https://openai.api2d.net/v1"
openai.api_key = "fk201020-Hva0Q8mWeiW00M4S6oygtOb52MqMmd9O"

def ymd(y, m, d):
    return '%d/%d/%d' % (y,m,d)
def ym(y, m):
    return '%d/%d' % (y,m)

def getYMStr(y, m):
    dt = datetime(y,m,1)
    return datetime.strftime(dt, '%Y/%m')
def getYMDStr(y, m, d):
    dt = datetime(y,m,d)
    return datetime.strftime(dt, '%Y/%m/%d')

def utc_now():
    utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
    dt = utc_now.astimezone(timezone(timedelta(hours=8)))
    dt = datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond)
    return dt

def setupDB(dbFile,useDateSerial=False):
    db = None
    query = Query()
    if useDateSerial:    
        serialization = SerializationMiddleware(JSONStorage)
        serialization.register_serializer(DateTimeSerializer(), 'TinyDate')
        db = TinyDB(dbFile,  storage=serialization)
    else:
        db = TinyDB(dbFile)
    return db, query
        
docsDB, docsQuery = setupDB('kms_docs.json', True)
docReadsDB, docReadsQuery = setupDB('kms_doc_reads.json', True)
recordsDB, recordsQuery = setupDB('pq_records.json', True)
orgsDB, orgsQuery = setupDB('kms_orgs.json')
gptDB, gptQuery = setupDB('gpt_answers.json', True)
dfmeaPartsDB, dfmeaPartsQuery = setupDB('dfmea_parts.json', True)
xtDocsDB, xtDocsQuery = setupDB('zxxt_docs.json', True)
flowsDB, flowsQuery = setupDB('oa_flows.json', True)
flowStepsDB, flowStepsQuery = setupDB('oa_flow_steps.json', True)
cpmsTasksDB, cpmsTasksQuery = setupDB('cpms_tasks.json', True)

# 设置页面宽度
st.set_page_config(page_title="研发信息化系统数据分析", layout="wide") 

def Line(page, data, title, height=500):
    tab1, tab2 = page.tabs(['图表','数据'])
    fig = px.line(data, x=0, y=1, title=title, line_shape='spline', height=height)
    tab1.plotly_chart(fig, use_container_width=True)
    #tab1.line_chart(data, use_container_width=True)
    #tab1.markdown(':sunglasses:')
    #tab1.markdown('This text is :red[colored red], and this is **:blue[colored]** and bold.')    
    tab2.dataframe(data, use_container_width=True)
def Bar(page, data, x, y, title='柱状图',ori='v'):
    tab1, tab2 = page.tabs(['图表','数据'])
    fig = px.bar(data, x=x, y=y, title=title, orientation=ori)
    tab1.plotly_chart(fig, use_container_width=True)
    tab2.dataframe(data, use_container_width=True)

def Bar2(container, data, x, y, text,  title='柱状图',ori='v',height=300):
    tab1, tab2 = container.tabs(['图表','数据'])    
    fig = px.bar(data, x=x, y=y, title=title, text=text, orientation=ori, height=height)
    if ori == 'v':
        fig = px.bar(data, x=x, y=y, title=title, text=text, orientation=ori, height=height)
    #fig.update_layout(xaxis_title=xTitle,yaxis_title=yTitle)
    #fig.update_traces(textposition="outside")
    fig.update_layout(
        yaxis={
            'tickformat': '.2f'
        }
    )
    tab1.plotly_chart(fig, use_container_width=True)
    tab2.dataframe(data, use_container_width=True)

def Bar3(container, data, x, y, text,  title='柱状图',ori='v',height=300, barmode='relative', color='None', lineCol=None):
    tab1, tab2 = container.tabs(['图表','数据']) 
    fig = None
    if ori == 'h':  
        fig = px.bar(data, x=x, y=y, title=title, text=text, orientation=ori, height=height, barmode=barmode, color=color,)
        fig.update_traces(textposition="outside")
        if lineCol:
            fig.add_trace(px.line(data, x=lineCol, y=y).data[0])  # 添加折线图
            fig.update_layout(yaxis2=dict(overlaying='x', side='top'))
    if ori == 'v':
        fig = px.bar(data, x=x, y=y, title=title, text=text, orientation=ori, height=height, barmode=barmode, color=color)
        fig.update_traces(textposition="outside")
        #if lineCol:
        #    fig.add_trace(px.line(data, x=x, y=lineCol).data[0])  # 添加折线图
        #    fig.update_layout(yaxis2=dict(overlaying='y', side='right'))
#fig.update_layout(xaxis_title=xTitle,yaxis_title=yTitle)
    fig.update_layout(
        yaxis={
            'tickformat': '.2f'
        }
    )
    tab1.plotly_chart(fig, use_container_width=True)
    tab2.dataframe(data, use_container_width=True)

def Pie(page, data, values, names, title='Pie', height=400):
    tab1, tab2 = page.tabs(['图表','数据'])
    fig = px.pie(data,values=values, names=names, title=title, height=height)
    tab1.plotly_chart(fig,use_container_width=True)
    tab2.dataframe(data, use_container_width=True)
def Bubble(page, data):
    fig = px.scatter(data.query('year==2007'),x='gdpPercap',y='lifeExp',size='pop',color='continent',hover_name='country',log_x=True,size_max=60)
    page.plotly_chart(fig,use_container_width=True)
def Scatter(page):
    page.plotly_chart(fig3, use_container_width=True)    
def Radar(page, data, title, r, theta, range_r):    
    fig = px.line_polar(data, title=title, r=r, theta=theta, line_close=True, range_r = range_r)
    page.plotly_chart(fig, use_container_width=True)

def askGPT(qKey, question, temp):
    dtNow = utc_now()
    answer = '' 
    mk = st.markdown(answer)       
    completion = openai.ChatCompletion.create(model="gpt-3.5-turbo-0613",
                                              messages=[{"role": "user", "content": question}], 
                                              temperature = temp, stream=True)  
    for chunk in completion:
        delta = chunk['choices'][0]['delta']
        #if 'role' in delta:
        #    answer += delta['role']+'：'
        if 'content' in delta:
            answer += delta['content']
        mk.markdown(answer)
    r = {'key':qKey, 'question':question, 'temperature':temp, 'answer':answer, 'time':dtNow}
    gptDB.insert(r)
    return r

def getGPTAnswer(qKey):
    reg = '.*%s.*' % qKey
    rs = gptDB.search(gptQuery.key.matches(reg))
    return rs

def getOrAskGPT(qKey, question, temp=0.7):
    #question
    if qKey and question:
        rs = getGPTAnswer(qKey)
        if rs:
            #st.write('answer from db')
            #st.markdown('问题：%s' % question)
            #for r in rs:
            #    st.markdown('%s' % r['time'])        
            #    st.markdown('%s' % r['answer'])
            r = rs[-1]
            st.markdown('%s' % r['time'])        
            st.markdown('%s' % r['answer'])
        else:
            st.markdown('暂无分析')
        if st.button('更新', key='gptAnswer_%s' % qKey, type='primary'):
            askGPT(qKey, question, temp)
    else:
        '进行分析的问题不可为空！'       

#st.sidebar.header('信息化系统数据分析')
s = st.sidebar.radio('研发信息化系统',('已建系统','在建系统','其他'))

deps = ['已建系统总览','KMS', 'CPMS', 'DFMEA', 'PQ', '在线协同', 'PQCP', '竞品系统']
devs = ['在建系统总览','ALM', 'BOM', 'SOA', 'IVX', '认证智能', 'DFMEA2.0', 'CPMS2.0', 'TC升级', '试验任务管理', '试验车管理', '项目成本分析']
cfgs = ['已建系统数据', 'GPT']

def sysPages(sysNames):
    tabs = st.tabs(sysNames)
    i = 0
    for sysName in sysNames:
        sysPage(sysName, tabs[i])
        i += 1
        
def average(vs):
    s = 0
    n = 0
    r = 0
    for v in vs:
        s = s + v
        n = n + 1
    if n > 0:
        r = float(s) / float(n)
    return r

kmsOrgs = orgsDB.all()
orgDict = {}
for org in kmsOrgs:
    orgDict[org['title']] = org['dept']

def getKmsDept(line, deptKey='部门'):
    title = line[deptKey] 
    r = title 
    if title in orgDict:
        r = orgDict[title]
    return r

@st.cache_data(ttl=600)
def getKmsOverview():
    dtNow = datetime.now()
    dtLast1 = dtNow - timedelta(30)
    dtLast2 = dtLast1 - timedelta(30)
    dtNow = datetime.strftime(dtNow, '%Y-%m-%d %H:%M')
    dtLast1 = datetime.strftime(dtLast1, '%Y-%m-%d %H:%M')
    dtLast2 = datetime.strftime(dtLast2, '%Y-%m-%d %H:%M')
    rs = docsDB.all()
    df = pd.DataFrame(rs).query('文档状态 == "发布"')
    allPubCount = len(df)
    tdf1 = df.query('(发布日期 < "%s") and (发布日期 > "%s")' % (dtNow, dtLast1))  
    pubCount1 = len(tdf1)
    tdf1 = tdf1.groupby('作者', as_index=False).agg('count')
    authorCount1 = len(tdf1)
    tdf2 = df.query('(发布日期 < "%s") and (发布日期 > "%s")' % (dtLast1, dtLast2))  
    pubCount2 = len(tdf2)
    tdf2 = tdf2.groupby('作者', as_index=False).agg('count')
    authorCount2 = len(tdf2) 

    tdf = df
    tdf['dept'] = tdf.apply(lambda x:getKmsDept(x,'所属部门'), axis=1)
    tdf1 = tdf.query('(发布日期 < "%s") and (发布日期 > "%s")' % (dtNow, dtLast1))
    tdf1 = tdf1.groupby('dept', as_index=False).agg('count').sort_values(by='fdId',ascending=False,inplace=False).iloc[:1]
    mvpDept = tdf1['dept'].values[0]
    mvpCount = int(tdf1['fdId'].values[0])

    deptCount1 = len(tdf1)
    #tdf2 = tdf.query('(发布日期 < "%s") and (发布日期 > "%s")' % (dtLast1, dtLast2))
    #tdf2 = tdf2.groupby('dept', as_index=False).agg('count')
    #deptCount2 = len(tdf1)
    #tdf1, tdf2    

    rs = docReadsDB.all()
    df = pd.DataFrame(rs)
    tdf1 = df.query('(阅读时间 < "%s") and (阅读时间 > "%s")' % (dtNow, dtLast1))  
    readCount1 = len(tdf1)
    tdf1 = tdf1.groupby('阅读人', as_index=False).agg('count')
    readerCount1 = len(tdf1)
    tdf2 = df.query('(阅读时间 < "%s") and (阅读时间 > "%s")' % (dtLast1, dtLast2))    
    readCount2 = len(tdf2)
    tdf2 = tdf2.groupby('阅读人', as_index=False).agg('count')
    readerCount2 = len(tdf2)

    tdf = df
    tdf['dept'] = tdf.apply(lambda x:getKmsDept(x,'部门'), axis=1)
    tdf1 = tdf.query('(阅读时间 < "%s") and (阅读时间 > "%s")' % (dtNow, dtLast1))
    tdf1 = tdf1.groupby('dept', as_index=False).agg('count').sort_values(by='fdId',ascending=False,inplace=False)
    tdf1 = tdf1.iloc[:1]
    mvrDept = tdf1['dept'].values[0]
    mvrCount = int(tdf1['序号'].values[0])

    return (dtNow, dtLast1, dtLast2, allPubCount, pubCount1, pubCount2, authorCount1, authorCount2, 
            readCount1, readCount2, readerCount1, readerCount2, mvpDept, mvpCount, mvrDept, mvrCount)
        
@st.cache_data(ttl=600)
def getPQOverview():
    dtNow = datetime.now()
    dtLast1 = dtNow - timedelta(30)
    dtLast2 = dtLast1 - timedelta(30)

    dtNow = datetime.strftime(dtNow, '%Y-%m-%d %H:%M')
    dtLast1 = datetime.strftime(dtLast1, '%Y-%m-%d %H:%M')
    dtLast2 = datetime.strftime(dtLast2, '%Y-%m-%d %H:%M')

    rs = recordsDB.all()
    df = pd.DataFrame(rs)
    
    tdf = df.query('(evaluationTime < "%s") and (evaluationTime > "%s")' % (dtNow, dtLast1))  
    evCount1 = len(tdf)
    tdf1 = tdf.groupby('evaluatorName', as_index=False).agg('count')
    erCount1 = len(tdf1)
    tdf1 = tdf.groupby('carModel', as_index=False).agg('count')
    cmCount1 = len(tdf1)
    carModels1 = list(tdf1['carModel']) 
    tdf = df.query('(evaluationTime < "%s") and (evaluationTime > "%s")' % (dtLast1, dtLast2))  
    evCount2 = len(tdf)
    tdf2 = tdf.groupby('evaluatorName', as_index=False).agg('count')
    erCount2 = len(tdf2)
    tdf2 = tdf.groupby('carModel', as_index=False).agg('count')
    cmCount2 = len(tdf2)
    carModels2 = list(tdf2['carModel'])
    return dtNow, dtLast1, dtLast2, evCount1, evCount2, erCount1, erCount2, cmCount1, cmCount2, carModels1, carModels2

@st.cache_data(ttl=600)
def getZxxtOverview():
    dtNow = datetime.now()
    dtLast1 = dtNow - timedelta(30)
    dtLast2 = dtLast1 - timedelta(30)
    dtNow = datetime.strftime(dtNow, '%Y-%m-%d %H:%M')
    dtLast1 = datetime.strftime(dtLast1, '%Y-%m-%d %H:%M')
    dtLast2 = datetime.strftime(dtLast2, '%Y-%m-%d %H:%M')
    rs = xtDocsDB.all()    
    df = pd.DataFrame(rs).query('statusDesc == "已发布"')
    allPubCount = len(df)

    tdf1 = df.query('(createdAt < "%s") and (createdAt > "%s")' % (dtNow, dtLast1))  
    pubCount1 = len(tdf1)    
    tdf2 = df.query('(createdAt < "%s") and (createdAt > "%s")' % (dtLast1, dtLast2))  
    pubCount2 = len(tdf2)
    pubDept1 = len(tdf1.groupby('deptName', as_index=False).agg('count'))
    pubDept2 = len(tdf2.groupby('deptName', as_index=False).agg('count'))

    puber1 = len(tdf1.groupby('createdName', as_index=False).agg('count'))
    puber2 = len(tdf2.groupby('createdName', as_index=False).agg('count'))

    tdf = df
    #tdf['dept'] = tdf.apply(lambda x:getKmsDept(x,'所属部门'), axis=1)
    tdf = tdf.query('(createdAt < "%s") and (createdAt > "%s")' % (dtNow, dtLast1))
    tdf1 = tdf.groupby('deptName', as_index=False).agg('count').sort_values(by='id',ascending=False,inplace=False).iloc[:1]
    mvpDept = tdf1['deptName'].values[0]
    mvpCount = int(tdf1['id'].values[0])
    tdf2 = tdf.groupby('createdName', as_index=False).agg('count').sort_values(by='id',ascending=False,inplace=False).iloc[:1]
    mvrUser = tdf2['createdName'].values[0]
    mvrCount = int(tdf2['id'].values[0])

    return (dtNow, dtLast1, dtLast2, allPubCount, pubCount1, pubCount2, 
            pubDept1, pubDept2, puber1, puber2, mvpDept, mvpCount, mvrUser, mvrCount)

def getOADeptName(line, userCol = 'starterName'):
    r = line['dept']    
    ndps = ['下部', '上部', '部件', '内外']
    dpUsers = {
        '赵倩楠':'车身部', '俞家乐':'热管理部', '陈凯琪':'智能网联部', '陈满':'智能网联部', '陈疆虎':'外饰部','肖龙盛':'内饰部',
        '尹金旭':'动力总成部', '岳华清':'电子电器部', '云松':'热管理部', '赵江圯':'车身部','钟金铭':'底盘部','陈凯08':'电控系统部',
        '刘锐01':'车身部', '李丹阳':'车身部', '黎咸龙':'内饰部', '王立军01':'底盘部', '龙永久':'动力总成部', '刘映鑫':'内饰部',
        '黎亭玮':'电控系统部', '孙宇然':'内饰部', '杨虎':'内饰部', '李鑫鹏':'内饰部', '王春晖':'底盘部'
               }
    dpUserName = line[userCol]
    if (r == '研发中心') and (dpUserName in dpUsers):
        r = dpUsers[dpUserName]
    else:
        dps = r.split('/')
        if '外饰/内外饰部' in r:
            r = '外饰部'
        elif ('内饰/内外饰部' in r) or ('门饰/内外饰部' in r) or ('门饰科/内外饰部' in r) or ('被动安全/内外饰部' in r) :
            r = '内饰部'
        else:
            for dp in dps:
                nb = False
                for ndp in ndps:
                    if ndp in dp:
                        nb = True
                        break
                if not nb:
                    if '部' in dp:
                        r = dp
                        break
    return r

@st.cache_data(ttl=3600)
def getOAOverview():
    dtNow = datetime.now()
    dtLast1 = dtNow - timedelta(30)
    dtLast2 = dtLast1 - timedelta(30)
    dtNow = datetime.strftime(dtNow, '%Y-%m-%d %H:%M')
    dtLast1 = datetime.strftime(dtLast1, '%Y-%m-%d %H:%M')
    dtLast2 = datetime.strftime(dtLast2, '%Y-%m-%d %H:%M')
    rs = flowsDB.search((flowsQuery.type.matches('.*设变.*')) & ~(flowsQuery.dept.matches('.*公用技术部.*')) & ~(flowsQuery.subject.matches('.*测试.*')))
    df = pd.DataFrame(rs)
    df['dept'] = df.apply(lambda x:getOADeptName(x), axis=1)

    df1 = df.query('(start < "%s") and (start > "%s")' % (dtNow, dtLast1))  
    df2 = df.query('(start < "%s") and (start > "%s")' % (dtLast1, dtLast2))
    flowCount1 = len(df1) 
    flowCount2 = len(df2)

    fdf1 = df1.query('finished == True')
    fdf2 = df2.query('finished == True')
    meanDt1 = round(fdf1['deltaTime'].agg('mean')/24, 1)
    meanDt2 = round(fdf2['deltaTime'].agg('mean')/24, 1)

    tdf = df1.groupby('dept', as_index=False).agg('count').sort_values(by='id',ascending=False,inplace=False).iloc[:1]
    maxFlowDept = tdf['dept'].values[0]
    maxFlowDeptCount = int(tdf['id'].values[0])

    tdf = df1.query('deltaTime > 24*15').groupby('dept', as_index=False).agg('count').sort_values(by='id',ascending=False,inplace=False)
    maxSlowFlowDept = tdf['dept'].values[0]
    maxSlowFlowDeptCount = int(tdf['id'].values[0])

    ndf1 = df1.query('finished == False')
    idleTime = datetime.now() - timedelta(5)
    idleTime = datetime.strftime(idleTime, '%Y-%m-%d %H:%M')
    tdf = ndf1.query('lastTime < "%s"' % idleTime)
    idleCount = len(tdf)  

    return (dtNow, dtLast1, dtLast2, flowCount1, flowCount2, meanDt1, meanDt2, 
            maxFlowDept, maxFlowDeptCount, maxSlowFlowDept,maxSlowFlowDeptCount, idleCount)

cpmsSession = requests.Session()
cpmsHeaders = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
               'Accept':'application/json, text/javascript, */*; q=0.01'}
def cpmsLogin():
    aid = '20051460'
    pwd = 'Syc@chery'
    loginUrl = "https://cpms.jetour.com.cn:5443/cpms/account/login"            
    loginData = 'account=%s&password=%s&encrypt=0&cname=&type=pwd' % (aid, pwd)
    r = cpmsSession.post(loginUrl, data=loginData, headers=cpmsHeaders, verify=True)
    r = r.json()
    loginResult = False
    if ('code' in r) and (r['code'] == "00000"):
        loginResult = True
    return loginResult

@st.cache_data(ttl=3600)
def getTasks(month):
    #'getPlans', month
    url = 'https://cpms.jetour.com.cn:5443/cpms/AppData/dataobjlist' 
    cdata = "class_id=0012&where=%5B%22(S_PLAN_MONTH%3D'JM"+month+"')%22%5D&maintain=&attr=feature+%3Bdata_obj_id+%3Bdata_obj_name+%3B\
        N_CREATEMETHOD+%3BG_SOURCE_OBJ+%3BS_CODE+%3BG_PRJ_ID+%3BS_PRJ_NAME+%3BS_NAME+%3BS_DELIVER_STAND+%3BS_PLAN_STATE+%3BD_DUE+%3BD_COMPLETED+%3B\
            S_EXECUTOR+%3BS_MONITOR+%3BG_TASK_ID+%3BS_SECTION_NAME+%3BG_SECTION_ID+%3BS_MODEL+%3BS_RANK+%3BS_DELIVER_TYPE+%3B\
                S_DUTY_TYPE+%3BN_FILE_COUNT+%3BG_DELAY_APPLY_TASK+%3BD_DELAY+%3BS_DELAY_NOTE&prjreltype=&order=S_CODE\
                    &_search=false&rows=3&page=1&sidx=&sord="
    r = cpmsSession.post(url, data=cdata, headers=cpmsHeaders)
    r = r.json()    
    objs = r['ret']['data']['ObjList']    
    objs
    plans = []
    if objs:
        for obj in objs:
            objAttrs = obj['ObjAttr']
            #tab.write(objAttrs)
            plan = {}
            b = True
            for objAttr in objAttrs:
                objName = objAttr['Name']
                objType = objAttr['Type']
                objValue = objAttr['Value']
                objDispName = objAttr['DispName']
                if objName in ['S_EXECUTOR', 'S_MONITOR']:
                    objValue = objValue.split(';')[1]    
                elif objType == '浮点数':
                    objValue = float(objValue)
                elif objType == '整数':
                    objValue = int(objValue)
                plan[objDispName] = objValue
                if (objDispName == '项目名称') and (objValue == '小计'):
                    b = False
                    break
            if b:
                plans.append(plan)
    return plans

@st.cache_data(ttl=3600)
def getPlans(month):
    #'getPlans', month
    url = 'https://cpms.jetour.com.cn:5443/cpms/AppData/dataobjlist'
    cdata = "class_id=0013&where=%5B%22(S_PLAN_MONTH%3D'JM"+month+"')%22%5D&maintain=&attr=feature+%3Bdata_obj_id+%3Bdata_obj_name+%3BN_CREATEMETHOD+%3BG_SOURCE_OBJ+%3B\
N_ORDER+%3BS_PRJ_CODE+%3BS_PRJ_NAME+%3BS_STATE+%3BS_P_LINE+%3BS_TRACK+%3BS_PD_NAME+%3BS_PM_NAME+%3BF_PLAN_SUM+%3BF_SB_COMPLETED+%3BF_COMPLETED+%3BF_DELAY+%3BF_IN_PROGRESS+%3B\
F_SCORE+%3BF_COMPLETED_LV+%3BF_C1+%3BF_D1+%3BF_S1+%3BF_C_LV1+%3BF_C2+%3BF_D2+%3BF_S2+%3BF_C_LV2+%3BF_C3+%3BF_D3+%3BF_S3+%3BF_C_LV3+%3BF_C4+%3BF_D4+%3BF_S4+%3B\
F_C_LV4+%3BF_C5+%3BF_D5+%3BF_S5+%3BF_C_LV5&prjreltype=&order=&_search=false&rows=100&page=1&sidx=N_ORDER%2CC_IS_SUM%2CS_PRJ_CODE&sord=asc"
    r = cpmsSession.post(url, data=cdata, headers=cpmsHeaders)
    r = r.json()
    objs = r['ret']['data']['ObjList']
    plans = []
    if objs:
        for obj in objs:
            objAttrs = obj['ObjAttr']
            #tab.write(objAttrs)
            plan = {}
            b = True
            for objAttr in objAttrs:
                objType = objAttr['Type']
                objValue = objAttr['Value']
                objDispName = objAttr['DispName']
                if objType == '浮点数':
                    objValue = float(objValue)
                elif objType == '整数':
                    objValue = int(objValue)
                plan[objDispName] = objValue
                if (objDispName == '项目名称') and (objValue == '小计'):
                    b = False
                    break
            if b:
                plans.append(plan)
    return plans

@st.cache_data(ttl=3600)
def getDepPlans(month):
    url = 'https://cpms.jetour.com.cn:5443/cpms/AppData/dataobjlist'
    cdata = "class_id=0011&where=%5B%22(S_PLAN_MONTH%3D'JM"+month+"')%22%5D&maintain=&attr=data_obj_id;data_obj_name;G_SOURCE_OBJ;\
S_SECTION_NAME;F_PLAN_SUM;F_SB_COMPLETED;F_COMPLETED;F_DELAY;F_SCORE;F_COMPLETED_LV&prjreltype=&order=&_search=false&rows=100&page=1&sidx=N_NO&sord=asc"
    r = cpmsSession.post(url, data=cdata, headers=cpmsHeaders, verify=True)
    r = r.json()
    objs = r['ret']['data']['ObjList']
    plans = []
    if objs:
        for obj in objs:
            objAttrs = obj['ObjAttr']
            plan = {}
            b = True
            for objAttr in objAttrs:
                objType = objAttr['Type']
                objValue = objAttr['Value']
                objName = objAttr['Name']
                objDispName = objAttr['DispName'] 
                if objType == '浮点数':
                    objValue = float(objValue)
                elif objType == '整数':
                    objValue = int(objValue)
                #plan[objName] = {'DispName':objDispName, 'Name':objName, 'Value':objValue}
                plan[objDispName] = objValue
                if (objDispName == '业务部门名称') and (objValue == '研发院'):
                    b = False
                    break
            if b:
                plans.append(plan)
    return plans

@st.cache_data(ttl=600)
def getCpmsOverview():
    dtNow = utc_now()
    y1 = dtNow.year
    m1 = dtNow.month
    m2 = m1 - 1
    y2 = y1
    if m1 == 1:
        m2 = 12
        y2 = y1 -1
    dtLast = datetime(y2, m2, 1)
    pm1 = datetime.strftime(dtNow, '%Y%m')
    pm2 = datetime.strftime(dtLast, '%Y%m')
    #tasks1 = getTasks(pm1)
    #'tasks', tasks1
    plans1 = getPlans(pm1)
    plans2 = getPlans(pm2)
    df1 = pd.DataFrame(plans1)#.query('状态=="执行"')
    df2 = pd.DataFrame(plans2)#.query('状态=="执行"')
    tdf = df1.sort_values(by='完成率',ascending=False)
    bestProj = tdf.iloc[:1]['项目名称'].values[0]
    bestRate = tdf.iloc[:1]['完成率'].values[0]       
    worstProj = tdf.iloc[-1:]['项目名称'].values[0]
    worstRate = tdf.iloc[-1:]['完成率'].values[0]

    mpt1 = df1.sort_values(by='积分',ascending=False,inplace=False).iloc[:1]
    mpb1 = df1.sort_values(by='积分',ascending=True,inplace=False).iloc[:1]
    mptn1 = mpt1['项目名称'].values[0]
    mptc1 = mpt1['积分'].values[0]
    mpbn1 = mpb1['项目名称'].values[0]
    mpbc1 = mpb1['积分'].values[0]

    planCount1 = df1['本月计划总数'].agg('sum')
    planCount2 = df2['本月计划总数'].agg('sum')
    planComp1 =  df1['当前已完成数量'].agg('sum') / planCount1
    depPlans1 = getDepPlans(pm1)
    depPlans2 = getDepPlans(pm2)
    df1 = pd.DataFrame(depPlans1)
    df2 = pd.DataFrame(depPlans2)
    delayCount1 = df1['延期数量'].agg(sum)
    delayCount2 = df2['延期数量'].agg(sum)
    dt1 = df1.sort_values(by='积分',ascending=False,inplace=False).iloc[:1]
    db1 = df1.sort_values(by='积分',ascending=True,inplace=False).iloc[:1]
    dtn1 = dt1['业务部门名称'].values[0]
    dtc1 = dt1['积分'].values[0]
    dbn1 = db1['业务部门名称'].values[0]
    dbc1 = db1['积分'].values[0]
    return (planCount1, planCount2, planComp1, delayCount1, delayCount2, dtn1, dtc1, dbn1, dbc1,
            bestProj, bestRate, worstProj, worstRate, mptn1, mptc1, mpbn1, mpbc1)

dfmeaSessionId = None
if 'dfmeaSessionId' in st.session_state:
    dfmeaSessionId = st.session_state['dfmeaSessionId']

dfmeaDepts = ['电器平台架构部', '动力总成部', '智能网联部', '热管理部', '车身部', 
              '底盘部','电子电器部', '电控系统部', '内饰部', '外饰部']

def dfmeaLogin():
    aid = '20156535'
    pwd = '20156535@Dfmea'
    loginUrl = "https://dfmea.jetour.com.cn:8443/DFMEA/login.do"
    headers = {"Content-Type": "application/json;charset=UTF-8"}
    loginData = {'username': aid, 'password': pwd}
    r = requests.post(loginUrl, data=json.dumps(loginData), headers=headers, verify=True)
    r = r.json()
    if ('code' in r) and (r['code'] == 200):
        result = r['result']
        dfmeaSessionId = result['sessionId']
        st.session_state['dfmeaSessionId'] = dfmeaSessionId
        st.experimental_rerun()

@st.cache_data(ttl=600)    
def loadUrlData(url, headers, data):
    r = requests.post(url, headers=headers, data=json.dumps(data), verify=True)
    r = r.json()
    return r
def showDfmeaPagedSheet(url, title='未知清单', data=None):
    #tab.subheader(title)
    postData = data
    headers = { 'Content-Type': 'application/json;charset=UTF-8', 'Cookie': "JSESSIONID_SHIRO=%s; SESSION=%s" % (dfmeaSessionId, dfmeaSessionId) }
    r = loadUrlData(url, headers, postData)
    rData = None
    if ('flag' in r) and r['flag']:
        rData = r['data']
    return rData 
       
@st.cache_data()
def getProjectDFMEAPageList():
    sheet = []
    pData = {'pageNo': 1, 'pageSize': 500, 'lifeState': "51", 'fmeaId': ""}
    #pData = {'pageNo': 1, 'pageSize': 500, 'fmeaId': ""}
    rData = showDfmeaPagedSheet('https://dfmea.jetour.com.cn:8443/DFMEA/projectDFMEA/getProjectDFMEAPageList.do', '项目DFMEA - 所有DEFMEA', pData)   
    if rData:
        ds = rData['data']
        for d in ds:
            record = {}
            record['id'] = d['fmeaId']
            record['系统'] = d['partName']
            record['创建者'] = d['dfmeaOwnerName']
            record['项目'] = d['projectNo']
            record['部门'] = d['departmentName']
            record['svpps'] = d['svpps']
            record['版本'] = d['version']
            record['创建时间'] = d['insertTime']
            record['更新时间'] = d['updateTime']
            record['parentId'] = d['parentFmeaId']
            sheet.append(record)
    return sheet


@st.cache_data()
def getPartsPageList():
    sheet = []
    pData = {'pageNo': 1, 'pageSize': 500}
    #pData = {'pageNo': 1, 'pageSize': 500, 'fmeaId': ""}
    rData = showDfmeaPagedSheet('https://dfmea.jetour.com.cn:8443/DFMEA/rdfmMyProject/getPartsPageList.do', 'DFMEA项目 - DEFMEA列表', pData)   
    if rData:
        ds = rData['data']
        for d in ds:
            record = {}
            record['id'] = d['fmeaId']
            record['工程师'] = d['engineerName']
            record['项目'] = d['projectNo']
            record['功能组'] = d['cocCode']
            record['svpps'] = d['svppsCode']
            record['FFC描述'] = d['ffcDescriptionCn']
            record['状态'] = d['taskHandOutStatus']
            record['任务分发时间'] = d['insertTime']
            record['实际完成时间'] = d['backupTime']
            sheet.append(record)
    return sheet

@st.cache_data()
def getMasterDFMEAPageList():
    sheet = []
    pData = {'pageNo': 1, 'pageSize': 500, 'lifeState': "51"}
    #pData = {'pageNo': 1, 'pageSize': 500}
    rData = showDfmeaPagedSheet('https://dfmea.jetour.com.cn:8443/DFMEA/masterFMEA/getMasterDFMEAPageList.do', 'Master DFMEA - 所有Master DEFMEA', pData)   
    if rData:
        ds = rData['data']
        for d in ds:
            record = {}
            record['id'] = d['fmeaId']
            record['系统'] = d['partName']
            record['创建者'] = d['dfmeaOwnerName']            
            record['部门'] = d['departmentName']
            record['svpps'] = d['svpps']
            record['版本'] = d['version']
            record['创建时间'] = d['insertTime']
            record['更新时间'] = d['updateTime']
            record['mainId'] = d['mainFmeaId']
            sheet.append(record)
    return sheet

@st.cache_data(ttl=3600)
def getProjectDfmeaRate():
    dfmeaCocFunc = lambda s:(s in dfmeaDepts)
    parts = dfmeaPartsDB.search((dfmeaPartsQuery.cocCode.test(dfmeaCocFunc)))    
    pdf = pd.DataFrame(parts)
    vs = {}
    tdf = pdf[['cocCode', 'taskHandOutStatus','partId']].groupby(['cocCode', 'taskHandOutStatus'], as_index=False).agg('count')
    cocs = list(tdf['cocCode'].values)
    stats = list(tdf['taskHandOutStatus'].values)
    cnts = list(tdf['partId'].values)
    i = 0
    n = len(cocs)
    for i in range(0, n):
        coc = cocs[i]
        stat = stats[i]
        cnt = cnts[i]
        r = [0,0,0,0]
        if coc in vs:
            r = vs[coc]
        if stat == '分析中':
            r[0] = cnt
        elif stat == '已分析':
            r[1] = cnt
        elif stat == '未分析':
            r[2] = cnt
        s = r[0] + r[1] + r[2]
        if s > 0:
            r[3] = float(r[0]+r[1]) / float(s)
        vs[coc] = r
    tdf = pd.DataFrame(vs)
    tdf = tdf.transpose()            
    tdf.columns=['分析中', '已分析', '未分析','分析率']
    tdf['部门'] = tdf.index
    tdf = tdf.sort_values(by='分析率', ascending=False)
    return tdf

def getDfmeaOverview():
    dtNow = datetime.now()
    dtLast1 = dtNow - timedelta(30)
    dtLast2 = dtLast1 - timedelta(30)

    dtNow = datetime.strftime(dtNow, '%Y-%m-%d %H:%M')
    dtLast1 = datetime.strftime(dtLast1, '%Y-%m-%d %H:%M')
    dtLast2 = datetime.strftime(dtLast2, '%Y-%m-%d %H:%M')
    
    #parts = dfmeaPartsDB.all() 
    dfmeaCocFunc = lambda s:(s in dfmeaDepts)
    parts = dfmeaPartsDB.search((dfmeaPartsQuery.cocCode.test(dfmeaCocFunc))) 
    projectDfmeaCount = len(parts)  
    
    mSheet = getMasterDFMEAPageList()    
    masterDfmeaCount = len(mSheet)

    pdf = pd.DataFrame(parts)
        
    tdf = pdf.groupby(['taskHandOutStatus'], as_index=False).agg('count')
    n1 = tdf.query('taskHandOutStatus == "分析中"')['partId'].values[0]
    n2 = tdf.query('taskHandOutStatus == "已分析"')['partId'].values[0]
    #n3 = tdf.query('taskHandOutStatus == "未分发"')['svpps'].values[0]
    n4 = tdf.query('taskHandOutStatus == "未分析"')['partId'].values[0]

    tdf = pdf.query('(backupTime < "%s") and (backupTime > "%s")' % (dtNow, dtLast1)) 
    bkCount1 = len(tdf)
    tdf = pdf.query('(backupTime < "%s") and (backupTime > "%s")' % (dtLast1, dtLast2)) 
    bkCount2 = len(tdf) 
    
    applyRate = float(n1+n2) / float(n1+n2+n4)
    
    tdf = pdf.groupby(['projectNo'], as_index=False).agg('count')
    projectCount = len(tdf)

    tdf = getProjectDfmeaRate()
    #df1 = tdf.iloc[:1]
    df1 = tdf.iloc[-1:]
    lRate = df1['分析率'].values[0]
    lDept = df1['部门'].values[0]

    return (masterDfmeaCount, projectCount, projectDfmeaCount, applyRate, bkCount1, bkCount2, lRate, lDept)

cpmsLogin()
if not dfmeaSessionId:  
    dfmeaLogin()  
 
def sysPage(sysName, tab):
    tab.subheader(sysName)
    #ep = tab.expander(sysName + '系统详细说明')   
    #ep.markdown(sysName + '系统的详细说明......................')
    if sysName == '已建系统总览':        
        sns = ['KMS', 'PQ' , 'CPMS', 'DFMEA', '在线协同', 'OA']
        tab.divider()   
        for sn in sns:         
            if sn == 'KMS':
                ca, col1, cb, col2, col3, col4, col5, col6, col7, col8 = tab.columns([1,2,2,5,5,5,5,5,10,10])
                col1.image('icon/%s.png' % sn, width=80)
                tab.divider()
                (dtNow, dtLast1, dtLast2, allPubCount, pubCount1, pubCount2, authorCount1, authorCount2,
                 readCount1, readCount2, readerCount1, readerCount2, mvpDept, mvpCount, mvrDept, mvrCount) = getKmsOverview() 
                col2.metric("总发布数", allPubCount, pubCount1)
                col3.metric("月度发布数", pubCount1, pubCount1-pubCount2)
                col4.metric("月度发布者数", authorCount1, authorCount1-authorCount2)                
                col5.metric("月度浏览数", readCount1, readCount1-readCount2)
                col6.metric("月度浏览者数", readerCount1, readerCount1-readerCount2)
                col7.metric("月度发布最多部门", mvpDept, mvpCount)
                col8.metric("月度浏览最多部门", mvrDept, mvrCount)
            elif sn == 'PQ':
                ca, col1, cb, col2, col3, col4, col5 = tab.columns([1,2,2,5,5,15,20])
                col1.image('icon/%s.png' % sn, width=80)
                tab.divider()
                dtNow, dtLast1, dtLast2, evCount1, evCount2, erCount1, erCount2, cmCount1, cmCount2, carModels1, carModels2 = getPQOverview() 
                col2.metric("月度评分数", evCount1, evCount1-evCount2)
                col3.metric("月度评分用户数", erCount1, erCount1-erCount2)
                col4.metric("月度评分车型数", cmCount1, cmCount1-cmCount2)
                col5.markdown('评分车型 :N :blue[本月：**%s**] :N :blue[上月：**%s**]' % ('** ， **'.join(carModels1), '** ， **'.join(carModels2)))            
            elif sn == 'CPMS':
                ca, col1, cb, col2, col3, col4, col5, col6, col7, col8 = tab.columns([1,2,2,5,5,5,8,2,10,10])
                col1.image('icon/%s.png' % sn, width=80)
                tab.divider()
                (planCount1, planCount2, planComp1, delayCount1, delayCount2, dtn1, dtc1, dbn1, dbc1,
                 bestProj, bestRate, worstProj, worstRate, mptn1, mptc1, mpbn1, mpbc1) = getCpmsOverview()
                col2.metric("月度计划任务数", planCount1, planCount1-planCount2)
                col3.metric("月度任务完成率", '%.2f%%' % (planComp1*100))
                col4.metric("月度任务延期数", '%d' % delayCount1, '%d' % (delayCount1-delayCount2), delta_color='inverse')
                #col5.metric("月度积分最高部门", dtn1, dtc1)
                #col6.metric("月度积分最低部门", dbn1, dbc1)
                col5.markdown('月度项目积分 :N :blue[**最高：%s（%s）**] :N :red[**最低：%s（%s）**]' 
                             % (mptn1, mptc1, mpbn1, mpbc1))
                col7.markdown('月度部门积分 :N :blue[**最高：%s（%s）**] :N :red[**最低：%s（%s）**]' 
                             % (dtn1, dtc1, dbn1, dbc1))
                #col7.metric("月度项目完成率", '%s(%.2f%%)' % (bestProj, bestRate*100) )
                col8.markdown('月度项目完成率 :N :blue[**最高：%s（%.2f%%）**] :N :red[**最低：%s（%.2f%%）**]' 
                             % (bestProj, bestRate*100, worstProj, worstRate*100))            
 
            elif sn == 'DFMEA':
                ca, col1, cb, col2, col3, col4, col5, col6, col7 = tab.columns([1,2,2,5,5,5,5,5,20])
                col1.image('icon/%s.png' % sn, width=80)
                tab.divider()
                (masterDfmeaCount, projectCount, projectDfmeaCount, applyRate, 
                 bkCount1, bkCount2, lRate, lDept) = getDfmeaOverview()
                col2.metric("家族DFMEA数", masterDfmeaCount)
                col3.metric("车型项目数", projectCount)
                col4.metric("项目DFMEA数", projectDfmeaCount)                
                col5.metric("总分析率", '%.2f%%' % (applyRate*100))
                col6.metric("月度分析完成数", bkCount1, bkCount1-bkCount2)
                #col7.metric("DFMEA分析率最低部门", '%s %.2f%%' % (lDept, lRate*100))
                col7.metric('分析率最低部门', ' %s(%.2f%%)' % (lDept, lRate*100))  
            elif sn == '在线协同':
                ca, col1, cb, col2, col3, col4, col5, col6, col7, col8 = tab.columns([1,2,2,5,5,5,5,5,10,10])
                col1.image('icon/%s.png' % sn, width=80)
                tab.divider()
                rs = xtDocsDB.all()
                (dtNow, dtLast1, dtLast2, allPubCount, pubCount1, pubCount2, 
                 pubDept1, pubDept2, puber1, puber2, mvpDept, mvpCount, mvrUser, mvrCount) = getZxxtOverview()
                #col1.metric("车型项目", "4", '1')
                #col2.metric("制造工程-模板库", "264", "35")
                #col3.metric("研发中心-模板库", "30", "5")
                #col4.metric("当前-待执行任务", "24", "3")
                #col5.metric("总超期任务", "10", "2", delta_color='inverse')
                #col6.metric("已发布-文档数", "14", "3")
                col2.metric("总文档数", allPubCount, pubCount1)
                col3.metric("月度发布文档数", pubCount1, pubCount1-pubCount2)
                col4.metric("月度发布部门数", pubDept1, pubDept1-pubDept2)
                col5.metric("月度发布用户数", puber1, puber1-puber2)
                col7.metric("月度发布文档最多部门", mvpDept, mvpCount)
                col8.metric("月度发布文档最多用户", mvrUser, mvrCount)
            elif sn == 'OA':
                from datetime import datetime
                with tab:
                    ca, col1, cb, col2, col3, col4, col5, col6, col7, col8 = st.columns([1,2,2,5,5,5,5,5,10,10])
                    col1.image('icon/%s.png' % sn, width=80)
                    st.divider()
                    (dtNow, dtLast1, dtLast2, flowCount1, flowCount2, meanDt1, meanDt2,
                    maxFlowDept, maxFlowDeptCount, maxSlowFlowDept,maxSlowFlowDeptCount, idleCount) = getOAOverview()
                    col2.metric("月度设变数", flowCount1, flowCount1-flowCount2, delta_color='inverse')
                    col3.metric("月度设变会签时长(日)", meanDt1, round(meanDt1-meanDt2, 1), delta_color='inverse')
                    col4.metric("月度异常设变数", idleCount, help='异常设变流程指超过5天无人响应的流程')
                    col7.metric("月度设变最多部门", maxFlowDept, maxFlowDeptCount, delta_color='inverse')
                    col8.metric("月度设变缓慢流程最多部门", maxSlowFlowDept, maxSlowFlowDeptCount, delta_color='inverse', help='缓慢流程指会签时间大于15天的流程')

                    if 0:
                        #########################
                        import pyecharts.options as opts
                        from pyecharts.charts import Calendar
                        import streamlit.components.v1 as components

                        dateTime1 = datetime(2023, 1, 1, 0,0,0)
                        dateTime2 = datetime(2023, 12, 31, 23,59,59)
                        rs = flowsDB.search((flowsQuery.start >= dateTime1) & (flowsQuery.start <= dateTime2) & (flowsQuery.type.matches('.*设变.*')) & ~(flowsQuery.dept.matches('.*公用技术部.*')) & ~(flowsQuery.subject.matches('.*测试.*')))      
                        df = pd.DataFrame(rs)
                        tdf = df.groupby(['start'], as_index=False).agg('count').sort_values(by='start',ascending=True,inplace=False)
                        heatmapData = []
                        startTimes = list(tdf['start'].values)
                        ids = list(tdf['id'].values)
                        for i in range(0, len(startTimes)):
                            stt = str(startTimes[i]).split('T')[0]
                            #stt = datetime.strptime(str(stt), '%Y-%m-%d %H:%M:%S').date
                            heatmapData.append([stt, int(ids[i])])  
                        heatmap = Calendar()
                        heatmap = heatmap.add(series_name="",yaxis_data=heatmapData,calendar_opts=opts.CalendarOpts(
                            pos_top="50",pos_left="30",pos_right="30",range_="2023",yearlabel_opts=opts.CalendarYearLabelOpts(is_show=True),),)
                        heatmap = heatmap.set_global_opts(title_opts=opts.TitleOpts(pos_top="0", pos_left="left",title="发起设变次数"),
                                                        visualmap_opts=opts.VisualMapOpts(max_=10, min_=0, orient="horizontal",is_piecewise=False),
                                                        ).render_embed()
                        components.html(heatmap,height=400, width=1000)
                        #########################

    elif sysName == 'KMS':
        @st.cache_data()
        def showKmsDocsDashboard():
            from datetime import datetime
            rs = docsDB.all()
            df = pd.DataFrame(rs)
            df['创建年'] = df.apply(lambda col: col['创建时间'].year, axis=1) 
            df['创建月'] = df.apply(lambda col: col['创建时间'].month, axis=1)
            df['创建日'] = df.apply(lambda col: col['创建时间'].day, axis=1)
            df['发布年'] = df.apply(lambda col: col['发布日期'].year, axis=1) 
            df['发布月'] = df.apply(lambda col: col['发布日期'].month, axis=1)
            df['发布日'] = df.apply(lambda col: col['发布日期'].day, axis=1)

            col1, col2, col3, col4 = st.columns(4)
            tdf = df
            tdf = tdf.groupby(['模板'], as_index=False).agg('count')
            tdf = tdf.sort_values(by='fdId',ascending=False,inplace=False).iloc[:10]
            Pie(col1, tdf, 'fdId', '模板', '知识库分布')
            s1 = str(tdf.rename(columns={'fdId':'数量'})[['模板','数量']].set_index('模板').to_dict())

            tdf = df
            tdf['dept'] = tdf.apply(lambda x:getKmsDept(x,'所属部门'), axis=1)
            tdf = tdf.groupby(['dept'], as_index=False).agg('count') 
            tdf = tdf.sort_values(by='fdId',ascending=False,inplace=False).iloc[:10]                
            Bar2(col2, tdf, 'dept', 'fdId', 'fdId','部门文档数', 'v', 400)
            s4 = str(tdf.rename(columns={'fdId':'数量', 'dept':'专业部门'})[['专业部门','数量']].set_index('专业部门').to_dict())

            tdf = df
            tdf = tdf.groupby(['创建者'], as_index=False).agg('count') 
            tdf = tdf.sort_values(by='fdId',ascending=False,inplace=False).iloc[:10]               
            Bar2(col3, tdf, '创建者', 'fdId', 'fdId','创建者文档数', 'v', 400)
            s5 = str(tdf.rename(columns={'fdId':'数量'})[['创建者','数量']].set_index('创建者').to_dict())

            tdf = df[['作者','浏览']]
            tdf = tdf.groupby(['作者'], as_index=False).agg('sum')
            tdf = tdf.sort_values(by='浏览',ascending=False,inplace=False).iloc[:10]
            Bar2(col4, tdf, '作者', '浏览', '浏览', '最受欢迎作者', 'v', 400)
            s2 = str(tdf.rename(columns={'浏览':'浏览量'})[['作者','浏览量']].set_index('作者').to_dict())
          

            col1, col2 = st.columns(2)
            tdf = df.groupby(['创建年', '创建月'], as_index=False).agg('count')                
            tdf['创建年月'] = tdf.apply(lambda col: ym(col['创建年'], col['创建月']), axis=1)
            Bar2(col1, tdf, '创建年月', 'fdId', 'fdId', '月创建数', 'v', 400)
            s3 = str(tdf.rename(columns={'fdId':'数量'})[['创建年月','数量']].set_index('创建年月').to_dict()) 

            tdf = df.groupby(['创建年', '创建月', '创建日'], as_index=False).agg('count')              
            tdf['创建日期'] = tdf.apply(lambda col: ymd(col['创建年'], col['创建月'], col['创建日']), axis=1)
            Bar2(col2, tdf, '创建日期', 'fdId', 'fdId','日创建数', 'v', 400)

            col1, col2 = st.columns(2)
            tdf = df.groupby(['发布年', '发布月'], as_index=False).agg('count')
            tdf = tdf[tdf['发布年'] < 2099]                
            tdf['发布年月'] = tdf.apply(lambda col: ym(col['发布年'], col['发布月']), axis=1)
            Bar2(col1, tdf, '发布年月', 'fdId', 'fdId', '月发布数', 'v', 400)
            tdf = df.groupby(['发布年', '发布月', '发布日'], as_index=False).agg('count') 
            tdf = tdf[tdf['发布年'] < 2099]              
            tdf['发布日期'] = tdf.apply(lambda col: ymd(col['发布年'], col['发布月'], col['发布日']), axis=1)
            Bar2(col2, tdf, '发布日期', 'fdId', 'fdId','日发布数', 'v', 400)            

            dtNow = datetime.now()
            dtY = dtNow.year
            dtM = dtNow.month
            mdf = df.query('发布年==%d and 发布月==%d' % (dtY, dtM))
            mdf['dept'] = mdf.apply(lambda x:getKmsDept(x,'所属部门'), axis=1)

            col1, col2, col3, col4 = st.columns(4)
            tdf = mdf
            tdf = tdf.groupby(['模板'], as_index=False).agg('count')
            tdf = tdf.sort_values(by='fdId',ascending=False,inplace=False).iloc[:10]
            Pie(col1, tdf, 'fdId', '模板', '月度知识库分布')
            s6 = str(tdf.rename(columns={'fdId':'数量'})[['模板','数量']].set_index('模板').to_dict())

            tdf = mdf
            tdf = tdf.groupby(['dept'], as_index=False).agg('count') 
            tdf = tdf.sort_values(by='fdId',ascending=False,inplace=False).iloc[:10]                
            Bar2(col2, tdf, 'dept', 'fdId', 'fdId','月度部门发布文档数', 'v', 400)
            
            tdf = mdf
            tdf = tdf.groupby(['创建者'], as_index=False).agg('count') 
            tdf = tdf.sort_values(by='fdId',ascending=False,inplace=False).iloc[:10]                
            Bar2(col3, tdf, '创建者', 'fdId', 'fdId','月度创建者发布文档数', 'v', 400)
            s8 = str(tdf.rename(columns={'fdId':'数量'})[['创建者','数量']].set_index('创建者').to_dict())

            tdf = mdf[['作者','浏览']]
            tdf = tdf.groupby(['作者'], as_index=False).agg('sum')
            tdf = tdf.sort_values(by='浏览',ascending=False,inplace=False).iloc[:10]
            Bar2(col4, tdf, '作者', '浏览', '浏览', '月度最受欢迎作者', 'v', 400)
            s7 = str(tdf.rename(columns={'浏览':'浏览量'})[['作者','浏览量']].set_index('作者').to_dict())

            nt = utc_now()
            #qk = 'kmsDocsDashboard_%s_%s_%s' % (nt.year, nt.month, nt.day)
            qk = 'kmsDocsDashboard'
            qs = '''按文档类型数量数据为：%s, 文档作者创建文档的总阅读数：%s, 按年月文档创建数量：%s, 
            专业部门创建的文档数：%s, 创建者创建的文档数：%s,
            本月新发布文档类型数量数据为：%s, 本月文档作者创建文档的阅读数：%s, 本月创建者创建的文档数：%s,
            ''' % (s1, s2, s3, s4, s5, s6, s7, s8)
            q = '以汽车研发设计行业大数据分析师的身份对以下括号中的数据进行分析，给出200字左右的综合性分析报告， 请用markdown语法输出内容, 请将重要或关键的内容用加粗红色字体表示出来 (%s)' % qs
            return qk, q

        @st.cache_data()
        def showKmsDocsActionDashboard():
            from datetime import datetime

            rs = docReadsDB.all()
            df = pd.DataFrame(rs)

            rs = docsDB.all()
            df1 = pd.DataFrame(rs)[['fdId','文档标题','作者','模板','所属部门']]           
            xdf = pd.merge(df, df1, on='fdId')

            tdf = xdf[['fdId', '文档标题']]#.query('(y == 2023) and (m == 7)')
            rdf1 = tdf.groupby(['文档标题'], as_index=False).agg('count').sort_values(by='fdId',ascending=False,inplace=False)[:10]

            tdf = xdf[['fdId', '文档标题', 'y', 'm']].query('(y == 2023) and (m == 7)')
            rdf2 = tdf.groupby(['文档标题'], as_index=False).agg('count').sort_values(by='fdId',ascending=False,inplace=False)[:10]

            col1, col2 = st.columns(2)
            Bar2(col1, rdf1, '文档标题', 'fdId', 'fdId', '总阅读量最多文档', 'v', 400)
            Bar2(col2, rdf2, '文档标题', 'fdId', 'fdId', '月度阅读量最多文档', 'v', 400)

            col1, col2 = st.columns(2)
            tdf = df.groupby(['y', 'm'], as_index=False).agg('count')
            tdf['ym'] = tdf.apply(lambda col: ym(col['y'], col['m']), axis=1)
            Bar2(col1, tdf, 'ym', 'fdId', 'fdId', '月阅读量', 'v', 400)
            s1 = str(tdf.rename(columns={'fdId':'数量', 'ym':'年月'})[['年月','数量']].set_index('年月').to_dict())

            tdf = df.groupby(['y', 'm', 'd'], as_index=False).agg('count')              
            tdf['ymd'] = tdf.apply(lambda col: ymd(col['y'], col['m'], col['d']), axis=1)
            Bar2(col2, tdf, 'ymd', 'fdId', 'fdId','日阅读量', 'v', 400)

            col1, col2 = st.columns(2)
            tdf = df
            tdf['dept'] = tdf.apply(lambda x:getKmsDept(x), axis=1)
            tdf = tdf.groupby(['dept'], as_index=False).agg('count') 
            tdf = tdf.sort_values(by='fdId',ascending=False,inplace=False).iloc[:20]               
            Bar2(col1, tdf, 'dept', 'fdId', 'fdId','部门总阅读量', 'v', 400)
            s2 = str(tdf.rename(columns={'fdId':'数量'})[['dept','数量']].set_index('dept').to_dict())

            tdf = df
            tdf = tdf.groupby(['阅读人'], as_index=False).agg('count') 
            tdf = tdf.sort_values(by='fdId',ascending=False,inplace=False).iloc[:20]                
            Bar2(col2, tdf, '阅读人', 'fdId', 'fdId','用户总阅读量', 'v', 400)
            s3 = str(tdf.rename(columns={'fdId':'数量'})[['阅读人','数量']].set_index('阅读人').to_dict())

            dtNow = datetime.now()
            dtY = dtNow.year
            dtM = dtNow.month
            col1, col2 = st.columns(2)
            tdf = df.query('y == %d and m == %d' % (dtY, dtM))
            tdf['dept'] = tdf.apply(lambda x:getKmsDept(x), axis=1)
            tdf = tdf.groupby(['dept'], as_index=False).agg('count')     
            tdf = tdf.sort_values(by='fdId',ascending=False,inplace=False).iloc[:20]                
            Bar2(col1, tdf, 'dept', 'fdId', 'fdId','部门阅读量(%d年%d月)' % (dtY, dtM), 'v', 400)
            s4 = str(tdf.rename(columns={'fdId':'数量'})[['dept','数量']].set_index('dept').to_dict())

            tdf = df.query('y == %d and m == %d' % (dtY, dtM))
            tdf = tdf.groupby(['阅读人'], as_index=False).agg('count') 
            tdf = tdf.sort_values(by='fdId',ascending=False,inplace=False).iloc[:20]                
            Bar2(col2, tdf, '阅读人', 'fdId', 'fdId','用户阅读量(%d年%d月)' % (dtY, dtM), 'v', 400)
            s5 = str(tdf.rename(columns={'fdId':'数量'})[['阅读人','数量']].set_index('阅读人').to_dict())

            mvDocs = ','.join(list(rdf1['文档标题'].values))
            mvDocsMonth = ','.join(list(rdf2['文档标题'].values))
            #mvDocs, mvDocsMonth

            nt = utc_now()
            #qk = 'kmsDocActionsDashboard_%s_%s_%s' % (nt.year, nt.month, nt.day)
            qk = 'kmsDocActionsDashboard'
            cym = '%d年%d月' % (dtY, dtM)
            qs = '文档的月阅读总量：%s, 文档按部门的阅读量：%s, 文档按阅读人的阅读量：%s, %s文档按部门的阅读量：%s, %s阅读文档最多的阅读人的阅读量：%s' % (s1, s2, s3, cym, s4, cym, s5)
            qs += ',总阅读量最多的10个文档按阅读量从高到低排序为这些文档：[%s], 本月阅读量最多的10个文档按阅读量从高到低排序为这些文档：[%s]' % (mvDocs, mvDocsMonth)
            q = '以汽车研发设计行业大数据分析师的身份对以下括号中的数据进行多维度分析挖掘，给出200字左右的综合性分析报告，另外通过对总阅读和本月阅读最多的文档也给出分析观点, 请用markdown语法输出内容, 请将分析内容中重要关键的内容用加粗红色字体表示出来 (%s)' % qs
            return qk, q
                    
        def showKmsOverview():
            col2, col3, col4, col5, col6, col7, col8 = st.columns([5,5,5,5,5,8,8])
            (dtNow, dtLast1, dtLast2, allPubCount, pubCount1, pubCount2, authorCount1, authorCount2,
             readCount1, readCount2, readerCount1, readerCount2, mvpDept, mvpCount, mvrDept, mvrCount) = getKmsOverview() 
            col2.metric("总发布数", allPubCount, pubCount1)
            col3.metric("月度发布数", pubCount1, pubCount1-pubCount2)
            col4.metric("月度发布者数", authorCount1, authorCount1-authorCount2)                
            col5.metric("月度浏览数", readCount1, readCount1-readCount2)
            col6.metric("月度浏览者数", readerCount1, readerCount1-readerCount2)
            col7.metric("月度发布最多部门", mvpDept, mvpCount)
            col8.metric("月度浏览最多部门", mvrDept, mvrCount)

            qs = '''
            截至目前，总文档发布数量为%d份,
            %s 至 %s 时间段内: 文档发布数量为%d份, 文档发布者数量为%d人,文档总浏览数为%d次, 文档总浏览者为%d人, 
            发布文档最多的部门是%s,共发布了%d份文档, 浏览文档最多的部门是%s,共浏览了%d次,
            %s 至 %s 时间段内: 文档发布数量为%d份, 文档发布者数量为%d人, 文档总浏览数为%d次, 文档总浏览者为%d人
            ''' % (allPubCount, 
                   dtLast1, dtNow, pubCount1, authorCount1, readCount1, readerCount1,mvpDept, mvpCount, mvrDept, mvrCount,
                   dtLast2, dtLast1, pubCount2, authorCount2, readCount2, readerCount2)
            q = '以汽车研发数据分析师的身份对以下括号中的数据进行分析挖掘，给出200字左右的本月数据研报和评论， 请用markdown语法输出内容, 请将重要或关键的内容用加粗红色字体表示出来 (%s)' % qs                
            nt = utc_now()
            qk = 'kmsOverview'
            return qk, q

        def fakeKmsDashboard():
            ep = tab.expander('系统运行分析')            
            col1, col2, col3 = ep.columns(3)        
            data = [(135, '金鑫'),(139, '李正谊'),(157, '金曙'),(234, '捷途管理员'),(645, '李明涛'),(7497, '黄杰')]
            Bar(col1, data, 0, 1, '最受欢迎作者','h')      
            data = [(22, '陈香澳'),(29, '刘京涛'),(40, '王涛'),(298, '戴源晨'),(405, '李明涛'),(1147, '黄杰')]
            Bar(col2, data, 0, 1, '发布量','h')  
            data = [{'数量':230, '类型':'项目成果库'}, {'数量':211, '类型':'专有技术库'}, {'数量':1567, '类型':'标准法规库'}, {'数量':7, '类型':'研发流程体系库'}, {'数量':298, '类型':'参考文件库'}, {'数量':25, '类型':'知识园地'}]
            Pie(col3, data, '数量', '类型', '知识库分布')
            
            ep.subheader('3月-知识发布')
            mDatas = [('1-3月发布',568,98),('更新',21,1),('阅读',3648,468)]
            n = len(mDatas)
            cols = ep.columns(n)
            for i in range(0,n):
                mData = mDatas[i]
                cols[i].metric(mData[0], mData[1], mData[2])
            col1, col2 = ep.columns(2) 
            data = [{'数量':83, '部门':'公用技术部'},{'数量':4, '部门':'车身部'}, {'数量':3, '部门':'项目管理部'}, {'数量':1, '部门':'底盘部'}, {'数量':1, '部门':'整车技术部'}, {'数量':1, '部门':'试验试制部'}, {'数量':1, '部门':'采购部'}]
            Pie(col1, data, '数量', '部门', '部门发布') 
            data = [('戴源晨',39), ('黄瑞',37),('楚伟峰',4), ('闫叶飞',3),('李明涛',2), ('黄杰',1),('李宗宝',1), ('袁丽',1), ('汪勇',1),('徐飞',1)]
            Bar(col2,data, 0, 1,'人员发布','v')
            
            ep.subheader('3月-知识应用')
            col1, col2 = ep.columns(2) 
            data = [(71,'试验试制部'),(62,'感官设计部'),(58,'底盘部'),(57,'热管理部'),(47,'公用技术部'),(40,'外饰部'),(40,'整车技术部'),(26,'内饰部'),(21,'电子电器部'),(13,'车身部'),(8,'品质保证部')]
            data.reverse()
            Bar(col1, data, 0, 1, '部门阅读量','h')
            data = [(39,'李振宇'),(28,'李海洋'),(28,'潘持恒'),(21,'陈疆虎'),(21,'陈光胜'),(17,'付望雨'),(16,'周康'),(16,'李宗宝'),(16,'张谢祥'),(12,'王星皓')]
            data.reverse()
            Bar(col2, data, 0, 1, '个人阅读量','h')
            
            data = [(214,'试验试制部'),(191,'热管理部'),(131,'外饰部'),(130,'内饰部'),(90,'底盘部'),(76,'公用技术部'),(73,'电子电器部'),(59,'动力总成部'),(32,'车身部'),(27,'智能网联部'),(27,'电控系统部')]
            data.reverse()
            Bar(col1, data, 0, 1, '部门搜索量','h')
            data = [(77,'李海洋'),(61,'周康'),(52,'陈疆虎'),(45,'胡珂'),(44,'李明涛'),(42,'王星皓'),(39,'姚传锐'),(35,'余建文'),(26,'汪守军'),(26,'曹庆新')]
            data.reverse()
            Bar(col2, data, 0, 1, '个人搜索量','h')
            
            ep.subheader('3月知识库运行趋势')
            data = [
            ('3/1',34),('3/2',13),('3/3',5),('3/4',39),('3/5',0),('3/6',40),('3/7',101),('3/8',73),
            ('3/9',10),('3/10',6),('3/11',1),('3/12',0),('3/13',65)
            ]
            Line(ep, data, '日新增发布数量', height=280)
            data = [
            ('3/1',160),('3/2',138),('3/3',109),('3/4',51),('3/5',9),('3/6',150),('3/7',85),('3/8',214),
            ('3/9',144),('3/10',107),('3/11',123),('3/12',0),('3/13',0)
            ]
            Line(ep, data, '日阅读用户数量', height=280)
            
            data = pd.DataFrame({
                'date':[
                '2021-10-01','2021-11-01','2021-12-01','2022-01-01','2022-02-01','2022-03-01',
                '2022-04-01','2022-05-01','2022-06-01','2022-07-01','2022-08-01','2022-09-01',
                '2022-10-01','2022-11-01','2022-12-01','2023-01-01','2023-02-01','2023-03-01'
                ],
                'values':[
                130, 60, 110, 150, 350, 180,
                230, 160, 880, 1120, 250, 380,
                330, 35, 100, 100, 1500, 810,
                ]
            })
            data['date'] = pd.to_datetime(data['date'])
            
            # 计算环比和同比
            data['month'] = data['date'].dt.month
            data['last_month_value'] = data['values'].shift(1)
            data['last_year_value'] = data['values'].shift(12)
            data['mom'] = (data['values'] - data['last_month_value']) / data['last_month_value']
            data['yoy'] = (data['values'] - data['last_year_value']) / data['last_year_value']        
            fig_mom = px.line(data, x='date', y='mom', title='环比', height=280, line_shape='spline')
            ep.plotly_chart(fig_mom)        
            fig_yoy = px.line(data, x='date', y='yoy', title='同比', height=280, line_shape='spline')
            ep.plotly_chart(fig_yoy)
            
            last_month_v = data['last_month_value'].iloc[-1]
            last_year_v = data['last_year_value'].iloc[-1]
            current_v = data['values'].iloc[-1]

            col1, col2, col3, col4, col5 = ep.columns(5)
            col1.metric('环比增长', f'{data["mom"].iloc[-1]:.2%}')
            col2.metric('同比增长', f'{data["yoy"].iloc[-1]:.2%}')
            col3.metric('上月数量', int(last_month_v))
            col4.metric('去年同期数量', int(last_year_v))
            col5.metric('本月数量', current_v)
            
            ep.dataframe(data,use_container_width=True)
            
            #ep.subheader('其他示例图表')
            #Pie(col2, px.data.tips(),'tip', 'day')
            #streamlit_echarts.st_pyecharts(c)           
            #Bubble(ep, px.data.gapminder())
            #Scatter(ep)

        ep = tab.expander('系统运行指标')
        with ep:
            tab1, tab2 = st.tabs(['指标','分析'])
            qk=q=''
            with tab1:
                qk, q = showKmsOverview()
            with tab2:
                getOrAskGPT(qk, q) 

        ep = tab.expander('知识文档统计')
        with ep:
            tab1, tab2 = st.tabs(['看板','分析'])
            qk=q=''
            with tab1:
                qk, q = showKmsDocsDashboard()
            with tab2:
                getOrAskGPT(qk, q)

        ep = tab.expander('知识文档操作统计')
        with ep:
            tab1, tab2 = st.tabs(['看板','分析'])
            qk=q=''
            with tab1:
                qk, q = showKmsDocsActionDashboard()                
            with tab2:
                getOrAskGPT(qk, q)

    elif sysName == '在线协同':  
        from datetime import datetime      
        ep = tab.expander('系统运行指标')
        with ep:
            (dtNow, dtLast1, dtLast2, allPubCount, pubCount1, pubCount2,
             pubDept1, pubDept2, puber1, puber2, mvpDept, mvpCount, mvrUser, mvrCount) = getZxxtOverview()
            col1, col2, col3, col4, col5, col6 = st.columns([5,5,5,5,8,13])
            col1.metric("总文档数", allPubCount, pubCount1)
            col2.metric("月度发布文档数", pubCount1, pubCount1-pubCount2)
            col3.metric("月度发布部门数", pubDept1, pubDept1-pubDept2)
            col4.metric("月度发布用户数", puber1, puber1-puber2)
            col5.metric("月度发布文档最多部门", mvpDept, mvpCount)
            col6.metric("月度发布文档最多用户", mvrUser, mvrCount)
        
        ep = tab.expander('系统运行分析')
        with ep:            
            rs = xtDocsDB.all()    
            df = pd.DataFrame(rs).query('statusDesc == "已发布"')
            df['y'] = df.apply(lambda x:datetime.strptime(x['publishTime'], '%Y-%m-%d %H:%M:%S').year, axis=1)
            df['m'] = df.apply(lambda x:datetime.strptime(x['publishTime'], '%Y-%m-%d %H:%M:%S').month, axis=1)
            df['d'] = df.apply(lambda x:datetime.strptime(x['publishTime'], '%Y-%m-%d %H:%M:%S').day, axis=1)
            df['ym'] = df.apply(lambda col:getYMStr(col['y'],col['m']), axis=1)
            df['ymd'] = df.apply(lambda col:getYMDStr(col['y'],col['m'],col['d']), axis=1)

            col1, col2 = st.columns(2) 
            tdf = df.groupby('folderName', as_index=False).agg('count').sort_values(by='id',ascending=False,inplace=False).iloc[:10] 
            Bar2(col1, tdf, 'folderName', 'id', 'id','按文档类型', 'v', 400)
            tdf = df.groupby('tmsProjectName', as_index=False).agg('count').sort_values(by='id',ascending=False,inplace=False).iloc[:10] 
            Bar2(col2, tdf, 'tmsProjectName', 'id', 'id','按车型项目', 'v', 400)
            
            col1, col2 = st.columns(2)
            tdf = df.groupby('deptName', as_index=False).agg('count').sort_values(by='id',ascending=False,inplace=False).iloc[:10] 
            Bar2(col1, tdf, 'deptName', 'id', 'id','部门创建文档', 'v', 400)
            tdf = df.groupby('createdName', as_index=False).agg('count').sort_values(by='id',ascending=False,inplace=False).iloc[:10] 
            Bar2(col2, tdf, 'createdName', 'id', 'id','用户创建文档', 'v', 400)
            
            col1, col2 = st.columns(2)
            tdf = df.groupby('ym', as_index=False).agg('count')#.sort_values(by='ym',ascending=True,inplace=False) 
            Bar2(col1, tdf, 'ym', 'id', 'id','月文档创建', 'v', 400)
            tdf = df.groupby('ymd', as_index=False).agg('count')#.sort_values(by='ymd',ascending=True,inplace=False) 
            Bar2(col2, tdf, 'ymd', 'id', 'id','日文档创建', 'v', 400)

            def fake():
                st.subheader('超期任务')
                col1, col2, col3 = st.columns(3)        
                data = [{'数量':4, '车型':'T1H PHEV'}, {'数量':6, '车型':'捷途'}]
                Pie(col1, data, '数量', '车型', '按车型')
                data = [{'数量':1, '模块':'数据校核'}, {'数量':7, '模块':'数据设计'},{'数量':0, '模块':'临时任务'},{'数量':1, '模块':'文档编制'},{'数量':1, '模块':'造型设计'},]
                Pie(col2, data, '数量', '模块', '按模块')        
                data = [('王丽丽',2), ('张保权',2),('丁宁',1), ('李坤',1),('张翔',1), ('胡军武',1),('徐浩',1), ('胡月胜',1)]
                Bar(col3,data, 0, 1,'按责任人','v')
            
                st.subheader('模块库')
                col1, col2 = st.columns(2)
                data = [{'数量':9, '类型':'项目类'}, {'数量':14, '类型':'设计类'},{'数量':7, '类型':'校核类'},{'数量':0, '类型':'试制试验'}]
                Pie(col1, data, '数量', '类型', '按类型')        
                data = [('项目管理',11), ('冲压规划',23),('焊装规划',52), ('涂装规划',45),('总装规划',68),('综合匹配',34), ('设备规划',28),('效率规划',3)]
                Bar(col2,data, 0, 1,'制造工程-模板库','v')
                
                col1, col2 = st.columns(2)
                col1.subheader('已发布文档')
                data = [{'数量':4, '类型':'工艺规划'}, {'数量':10, '类型':'研发中心'}]
                Pie(col1, data, '数量', '类型', '按类型')
                col2.subheader('协同空间-数据')
                data = [{'数量':220, '类型':'基线数据'}, {'数量':24, '类型':'工作中'}]
                Pie(col2, data, '数量', '类型', '按类型')
    elif sysName == 'CPMS':  
        from datetime import datetime           
        ep = tab.expander('系统运行指标')
        with ep:
            tab1, tab2 = st.tabs(['指标','分析'])
            qk=q=''
            with tab1:
                col2, col3, col4, col5, col6, col7, col8 = st.columns([5,5,5,8,2,10,10])
                (planCount1, planCount2, planComp1, delayCount1, delayCount2, dtn1, dtc1, dbn1, dbc1,
                bestProj, bestRate, worstProj, worstRate, mptn1, mptc1, mpbn1, mpbc1) = getCpmsOverview()
                col2.metric("月度计划任务数", planCount1, planCount1-planCount2)
                col3.metric("月度任务完成率", '%.2f%%' % (planComp1*100))
                col4.metric("月度任务延期数", '%d' % delayCount1, '%d' % (delayCount1-delayCount2), delta_color='inverse')
                #col5.metric("月度积分最高部门", dtn1, dtc1)
                #col6.metric("月度积分最低部门", dbn1, dbc1)
                col5.markdown('月度项目积分 :N :blue[**最高：%s（%s）**] :N :red[**最低：%s（%s）**]' 
                                % (mptn1, mptc1, mpbn1, mpbc1))
                col7.markdown('月度部门积分 :N :blue[**最高：%s（%s）**] :N :red[**最低：%s（%s）**]' 
                                % (dtn1, dtc1, dbn1, dbc1))
                #col7.metric("月度项目完成率", '%s(%.2f%%)' % (bestProj, bestRate*100) )
                col8.markdown('月度项目完成率 :N :blue[**最高：%s（%.2f%%）**] :N :red[**最低：%s（%.2f%%）**]' 
                                % (bestProj, bestRate*100, worstProj, worstRate*100))
                qs = '''
                以下是车型项目月度计划的执行情况：
                这个月: 月度计划共%d个, 目前月度计划完成率为%.2f%%, 月度计划延期%d个;
                上个月: 月度计划共%d个, 月度计划延期%d个; 
                这个月月度计划积分情况: 最高的部门为%s, 积分为%d, 最低的部门为%s,积分为%d,最高的项目为%s, 积分为%d, 最低的项目为%s,积分为%d;
                这个月月度计划完成率情况: 最高的项目为%s, 完成率为%.2f%%, 完成率最低的项目为%s, 完成率为%.2f%% 
                ''' % (planCount1, planComp1*100, delayCount1, planCount2, delayCount2, dtn1, dtc1, dbn1, dbc1, 
                       mptn1, mptc1, mpbn1, mpbc1, bestProj, bestRate*100, worstProj, worstRate*100)
                q = '以汽车研发项目分析师的身份对以下括号中的数据进行深度分析，给出200字左右的本月数据研报和评论，请用markdown语法输出内容, 请将重要或关键的内容用加粗红色字体表示出来 (%s)' % qs                
                qk = 'cpmsOverview'
            with tab2:               
                getOrAskGPT(qk, q)             

        ep = tab.expander('系统运行分析')
        with ep:        
            month = st.selectbox('选择计划月度', 
                                    ['202208','202209','202210','202211','202212',
                                    '202301','202302','202303','202304','202305','202306','202307'])
            plans = getPlans(month)
            st.subheader('项目任务总览')
            if plans:
                df = pd.DataFrame(plans)#.query('状态=="执行"')
                cols = st.columns(4)     
                tdf = df.sort_values(by='本月计划总数',ascending=False,inplace=False)
                Pie(cols[0], tdf, '本月计划总数', '项目名称', '项目任务数')
                tdf = df.groupby(['赛道'], as_index=False).agg('sum',numeric_only=True).sort_values(by='本月计划总数',ascending=False,inplace=False)
                Pie(cols[1], tdf, '本月计划总数', '赛道', '赛道任务数')           
                tdf = df.groupby(['项目总监'], as_index=False).agg('sum',numeric_only=True).sort_values(by='本月计划总数',ascending=False,inplace=False).iloc[:10]                
                Pie(cols[2], tdf, '本月计划总数', '项目总监', '项目总监任务数')
                tdf = df.groupby(['项目经理'], as_index=False).agg('sum',numeric_only=True).sort_values(by='本月计划总数',ascending=False,inplace=False).iloc[:10]
                Pie(cols[3], tdf, '本月计划总数', '项目经理', '项目经理任务数')                
                
                cols = st.columns(4)
                tdf = df.groupby(['项目名称'], as_index=False).agg('sum',numeric_only=True).sort_values(by='积分',ascending=False,inplace=False).sort_values(by='积分',ascending=True,inplace=False).iloc[-10:]
                fig = px.bar(tdf, x='积分', y='项目名称',title='项目积分排行',text='积分', orientation='h', height=400)
                cols[0].plotly_chart(fig,use_container_width=True)
                tdf = df.groupby(['赛道'], as_index=False).agg('sum',numeric_only=True).sort_values(by='积分',ascending=False,inplace=False).sort_values(by='积分',ascending=True,inplace=False).iloc[-10:]
                fig = px.bar(tdf, x='积分', y='赛道',title='赛道积分排行',text='积分',orientation='h', height=400)
                cols[1].plotly_chart(fig,use_container_width=True)
                tdf = df.groupby(['项目总监'], as_index=False).agg('sum',numeric_only=True).sort_values(by='积分',ascending=False,inplace=False).sort_values(by='积分',ascending=True,inplace=False).iloc[-10:]
                fig = px.bar(tdf, x='积分', y='项目总监',title='项目总监积分排行',text='积分',orientation='h', height=400)
                cols[2].plotly_chart(fig,use_container_width=True)
                tdf = df.groupby(['项目经理'], as_index=False).agg('sum',numeric_only=True).sort_values(by='积分',ascending=False,inplace=False).sort_values(by='积分',ascending=True,inplace=False).iloc[-10:]
                fig = px.bar(tdf, x='积分', y='项目经理',title='项目经理积分排行',text='积分',orientation='h', height=400)
                cols[3].plotly_chart(fig,use_container_width=True)
                
                
                cols = st.columns(4)
                tdf = df.query("延期数量 > 0").sort_values(by='延期数量',ascending=False,inplace=False)              
                Bar2(cols[0], tdf, '项目名称', '延期数量', '延期数量','项目任务延期数量', 'v', 400)
                tdf = df.query("延期数量 > 0").groupby(by='赛道', as_index=False).agg('count').sort_values(by='延期数量',ascending=False,inplace=False)              
                Bar2(cols[1], tdf, '赛道', '延期数量', '延期数量','赛道任务延期数量', 'v', 400)
                tdf = df.query("延期数量 > 0").groupby(by='项目总监', as_index=False).agg('count').sort_values(by='延期数量',ascending=False,inplace=False)              
                Bar2(cols[2], tdf, '项目总监', '延期数量', '延期数量','项目总监延期数量', 'v', 400)
                tdf = df.query("延期数量 > 0").groupby(by='项目经理', as_index=False).agg('count').sort_values(by='延期数量',ascending=False,inplace=False)              
                Bar2(cols[3], tdf, '项目经理', '延期数量', '延期数量','项目经理延期数量', 'v', 400)

                cols = st.columns(4)
                tdf = df.sort_values(by='完成率',ascending=False,inplace=False)
                tdf['完成率'] = tdf.apply(lambda x:'%s%%' % round(x['完成率']*100,2), axis=1)
                Bar2(cols[0], tdf, '项目名称', '完成率', '完成率','项目任务完成率', 'v', 400) 
                tdf = df.groupby(['赛道'], as_index=False).agg('mean',numeric_only=True).sort_values(by='完成率',ascending=False,inplace=False)
                tdf['完成率'] = tdf.apply(lambda x:'%s%%' % round(x['完成率']*100,2), axis=1)
                Bar2(cols[1], tdf, '赛道', '完成率', '完成率','赛道任务完成率', 'v', 400)
                tdf = df.groupby(['项目总监'], as_index=False).agg('mean',numeric_only=True).sort_values(by='完成率',ascending=False,inplace=False)
                tdf['完成率'] = tdf.apply(lambda x:'%s%%' % round(x['完成率']*100,2), axis=1)
                Bar2(cols[2], tdf, '项目总监', '完成率', '完成率','项目总监任务完成率', 'v', 400)
                tdf = df.groupby(['项目经理'], as_index=False).agg('mean',numeric_only=True).sort_values(by='完成率',ascending=False,inplace=False)
                tdf['完成率'] = tdf.apply(lambda x:'%s%%' % round(x['完成率']*100,2), axis=1)
                Bar2(cols[3], tdf, '项目经理', '完成率', '完成率','项目经理任务完成率', 'v', 400)

            plans = getDepPlans(month)
            st.subheader('项目任务部门执行情况')
            if plans:
                df = pd.DataFrame(plans)
                cols = st.columns(3)
                tdf = df.sort_values(by='本月计划总数',ascending=False,inplace=False).iloc[:10]                
                Pie(cols[0], tdf, '本月计划总数', '业务部门名称', '业务部门任务数')

                tdf = df.groupby(['业务部门名称'], as_index=False).agg('sum',numeric_only=True).sort_values(by='积分',ascending=True,inplace=False).iloc[-10:]#.sort_values(by='积分',ascending=True,inplace=False)                
                Bar2(cols[1], tdf, '积分', '业务部门名称', '积分','业务部门积分前十名', 'h', 400)

                tdf = df.groupby(['业务部门名称'], as_index=False).agg('sum',numeric_only=True).sort_values(by='积分',ascending=False,inplace=False).iloc[-10:]#.sort_values(by='积分',ascending=True,inplace=False)                
                Bar2(cols[2], tdf, '积分', '业务部门名称', '积分','业务部门积分后十名', 'h', 400)

                cols = st.columns(2)
                tdf = df.sort_values(by='完成率',ascending=False,inplace=False).iloc[0:20]
                tdf['完成率'] = tdf.apply(lambda x:'%s%%' % round(x['完成率']*100,2), axis=1)
                Bar2(cols[0], tdf, '业务部门名称', '完成率', '完成率','业务部门任务完成率', 'v', 400)

                tdf = df.query("延期数量 > 0").groupby(['业务部门名称'], as_index=False).agg('sum',numeric_only=True).sort_values(by='延期数量',ascending=False,inplace=False)#.iloc[0:10]#.sort_values(by='积分',ascending=True,inplace=False)                
                Bar2(cols[1], tdf, '业务部门名称', '延期数量', '延期数量','业务部门延期数量', 'v', 400)
            else:
                st.write('无月度项目计划数据')            
        
        with tab.expander('计划任务分析'):            
            #dateTime1 = datetime(2023, 6, 1, 0,0,0)
            #dateTime2 = datetime(2023, 7, 1, 0,0,0)
            #rs = cpmsTasksDB.search((cpmsTasksQuery.计划完成日期 >= dateTime1) & (cpmsTasksQuery.计划完成日期 < dateTime2)) 
            rs = cpmsTasksDB.all()
            df = pd.DataFrame(rs)
            df['y'] = df.apply(lambda x:x['计划完成日期'].year, axis=1)
            df['m'] = df.apply(lambda x:x['计划完成日期'].month, axis=1)
            df['d'] = df.apply(lambda x:x['计划完成日期'].day, axis=1)
            df['ym'] = df.apply(lambda col:getYMStr(col['y'],col['m']), axis=1)
            df['ymd'] = df.apply(lambda col:getYMDStr(col['y'],col['m'],col['d']), axis=1)
            #df
            df = df[['y', 'm', 'd', 'ym', 'ymd', '计划完成日期', '实际完成日期', '执行人','六大模块','监督人','月度计划内容',
                    '计划状态','项目名称','项目对象标识','工作等级','责任部门','责任部门标识', '交付物类型']]
            df = df.query('ym > "202212"')
            def fixColName(fixDf, colId, colName):
                colNameDict = {}
                tdf = fixDf[[colId, colName,'ym','y']]
                tdf = tdf.groupby([colId, colName,'ym'], as_index=False).agg('count').sort_values(by='ym',ascending=True,inplace=False)
                vs = list(tdf.values)
                for v in vs:
                    vcId = v[0]
                    vcName = v[1] 
                    colNameDict[vcId] = vcName
                def getCurrentColName(col):
                    cName = col[colName]
                    cId = col[colId]
                    if cId in colNameDict.keys():
                        return colNameDict[cId]
                    else:
                        return cName
                fixDf[colName] = fixDf.apply(lambda col:getCurrentColName(col), axis=1)                
            fixColName(df, '责任部门标识','责任部门')
            fixColName(df, '项目对象标识','项目名称')

            def fixCpmsActDate(col):
                py = col['y']
                pm = col['m']
                dt = col['实际完成日期']
                pt = col['计划完成日期']
                ps = col['计划状态']
                r = dt
                if not dt:
                    if ps == '已完成':
                        #r = 'fixed [%s] - %s' % (dt, pt)  
                        r = pt
                    else:
                        r = ''
                elif (type(dt) is str):
                    #r = 'fixing - %s' % dt
                    r = dt
                    dts = dt.split('-')
                    if len(dts) == 2:
                        dy = py
                        dm = int(dts[0])
                        dd = int (dts[1])
                        if abs(dm-pm) >= 11:
                            if pm <= 1:
                                dy = py - 1
                            elif pm >= 11:
                                dy = py + 1
                        ft = datetime(dy, dm, dd)
                        #r = 'fixed [%s] -> %s' % (dt, ft)
                        r = ft
                return r
            df['实际完成日期'] = df.apply(lambda col:fixCpmsActDate(col), axis=1)
            df

            #tdf = df.groupby(by='六大模块', as_index=False).agg('count')
            #tdf

            col1, col2 = st.columns(2)
            tdf = df.groupby('ym', as_index=False).agg('count')#.sort_values(by='ym',ascending=True,inplace=False) 
            Bar2(col1, tdf, 'ym', 'y', 'y','月计划任务数', 'v', 400)
            tdf = df.groupby('ymd', as_index=False).agg('count')#.sort_values(by='ymd',ascending=True,inplace=False) 
            Bar2(col2, tdf, 'ymd', 'y', 'y','日计划任务数', 'v', 400)

            @st.cache_data()
            def getCpmsPlansActData(df, col, name):
                ds = []
                try:
                    if col and name:
                        q = '%s=="%s"' % (col, name)
                        df = df.query(q)
                    else:
                        name = '总计'
                    tdf1 = df.groupby(['ym'], as_index=False).agg('count')
                    tdf2 = df.query('实际完成日期 > 计划完成日期').groupby(['ym'], as_index=False).agg('count')
                    tdf3 = df.query('计划状态 == "已完成"').groupby(['ym'], as_index=False).agg('count')
                    vs1 = list(tdf1.values)
                    vs2 = list(tdf2.values)
                    vs3 = list(tdf3.values)
                    rs = {}
                    for v in vs1:
                        ym = v[0]
                        cnt = v[1]
                        r = [cnt, 0, 0, 0, 0]
                        if ym in rs:
                            r = rs[ym]
                            r[0] = cnt
                        rs[ym] = r
                    for v in vs2:
                        ym = v[0]
                        cnt = v[1]
                        r = [0, cnt, 0, 0, 0]
                        if ym in rs:
                            r = rs[ym]
                            r[1] = cnt
                        rs[ym] = r 
                    for v in vs3:
                        ym = v[0]
                        cnt = v[1]
                        r = [0, 0, cnt, 0, 0]
                        if ym in rs:
                            r = rs[ym]
                            r[2] = cnt
                        rs[ym] = r
                    for k in rs:
                        r = rs[k]
                        cAll = r[0]
                        cDelay = r[1]
                        cDone = r[2]
                        if cAll > 0:
                            r[3] = float(cDone) / float(cAll) * 100
                            r[4] = float(cDone - cDelay) / float(cAll) * 100
                    for k in rs.keys():
                        v = rs[k]
                        #ds.append({'月度':k, '任务总数':v[0], '延期数':v[1], '完成数':v[2], '完成率':v[3], 'type':'完成率'})
                        ds.append({'月度':k, '任务总数':v[0], '延期数':v[1], '完成数':v[2], '完成率':v[4], 'name':name})                
                    #ddf = pd.DataFrame(ds)
                except:
                    pass
                return ds
            
            

            dsAll = []
            #ds = getCpmsPlansActData(df, None, None)
            #dsAll += ds
            col = '项目名称'
            names = list(df.groupby(by=col, as_index=False).agg('count')[col])
            for name in names:
                ds = getCpmsPlansActData(df, col, name)
                dsAll += ds
            ddf = pd.DataFrame(dsAll).query('任务总数 > 100').sort_values(by='月度',ascending=True,inplace=False) 
            fig = px.line(ddf, x='月度', y='完成率', color='name', title='月度计划按时完成率', height=800, line_shape='spline')
            st.plotly_chart(fig)

            rs = ddf.values
            qk = 'CpmsTaskStatus'
            q = '''你是一名资深的数据分析师，拥有敏锐的数据洞察能力，请对以下括号中项目任务完成情况的数据进行分析，给出300字尖锐和精辟的项目计划数据分析研报及观点，
            请用markdown语法输出内容, 请将重要或关键的内容用加粗红色字体表示出来,括号中数据项分别为[月度,任务总数,任务延期数,任务完成数,按时完成率,项目名称],
            (%s)''' % rs
            getOrAskGPT(qk, q)

            dsAll = []
            #ds = getCpmsPlansActData(df, None, None)
            #dsAll += ds
            col = '六大模块'
            names = list(df.groupby(by=col, as_index=False).agg('count')[col])
            for name in names:
                ds = getCpmsPlansActData(df, col, name)
                dsAll += ds
            ddf = pd.DataFrame(dsAll).query('任务总数 > 50').sort_values(by='月度',ascending=True,inplace=False) 
            fig = px.line(ddf, x='月度', y='完成率', color='name', title='月度计划按时完成率', height=800, line_shape='spline')
            st.plotly_chart(fig)

            rs = ddf.values
            qk = 'CpmsTaskStatus_modules'
            q = '''你是一名资深的数据分析师，拥有敏锐的数据洞察能力，请对以下括号中六大模块任务完成情况的数据进行分析，给出300字尖锐和精辟的项目计划数据分析研报及观点，
            请用markdown语法输出内容, 请将重要或关键的内容用加粗红色字体表示出来,括号中数据项分别为[月度,任务总数,任务延期数,任务完成数,按时完成率,项目名称],
            (%s)''' % rs
            getOrAskGPT(qk, q)


            #tdf = df.query('实际完成日期 > 计划完成日期')#.groupby('ym', as_index=False)#.agg('count')#.sort_values(by='ym',ascending=True,inplace=False) 
            #tdf
            #Bar2(col1, tdf, 'ym', 'y', 'y','月计划任务数', 'v', 400)

    elif sysName == 'DFMEA':
        ep = tab.expander('系统运行指标')
        col2, col3, col4, col5, col6, col7 = ep.columns([5,5,5,5,5,16])
        (masterDfmeaCount, projectCount, projectDfmeaCount, applyRate,
         bkCount1, bkCount2, lRate, lDept) = getDfmeaOverview()
        col2.metric("家族DFMEA数", masterDfmeaCount)
        col3.metric("项目数", projectCount)
        col4.metric("项目DFMEA数", projectDfmeaCount)                
        col5.metric("总分析率", '%.2f%%' % (applyRate*100))
        col6.metric("月度分析完成数", bkCount1, bkCount1-bkCount2)
        col7.metric('分析率最低部门', ' %s(%.2f%%)' % (lDept, lRate*100))

        def showApp():
            dfmeaCocFunc = lambda s:(s in dfmeaDepts)
            parts = dfmeaPartsDB.search((dfmeaPartsQuery.cocCode.test(dfmeaCocFunc)))
            df = pd.DataFrame(parts)

            #sheet = []            
            #pData = {'pageNo': 1, 'pageSize': 100, 'businessType': "", 'projectStatus': ""}
            #rData = showDfmeaPagedSheet('https://dfmea.jetour.com.cn:8443/DFMEA/rdfmMyProject/getMyProjectPageList.do','我的项目 - DEFMEA项目', pData)
            #if rData:
            #    ds = rData['data']
            #    for d in ds:
            #        projectNo = d['projectNo']
            #        if projectNo == 'test1':
            #            continue
            #        pData = {'projectSn': projectNo, 'pageNo': 1, 'pageSize': 100}
            #        rData = showDfmeaPagedSheet('https://dfmea.jetour.com.cn:8443/DFMEA/rdfmMyProject/getPartsPageList.do','DEFMEA项目 - %s' % projectNo, pData)
            #        rds = rData['data']
            #        for rd in rds:
            #            sheet.append({'项目':projectNo, '部门':rd['cocCode'], '工程师':rd['engineerName'], '状态':rd['taskHandOutStatus']})
            #df =pd.DataFrame(sheet)

            cols = st.columns(2)
            df1 = df.groupby(['projectNo'], as_index=False).agg('count').sort_values(by='taskHandOutStatus',ascending=False,inplace=False).iloc[:10]
            Pie(cols[0], df1, 'taskHandOutStatus', 'projectNo', '项目分布')
            df2 = df.groupby(['cocCode'], as_index=False).agg('count').sort_values(by='taskHandOutStatus',ascending=False,inplace=False).iloc[:10]
            Pie(cols[1], df2, 'taskHandOutStatus', 'cocCode', '部门分布')
            df3 = df.groupby(['taskHandOutStatus'], as_index=False).agg('count').sort_values(by='projectNo',ascending=False,inplace=False).iloc[:10]
            Pie(cols[0], df3, 'projectNo', 'taskHandOutStatus', '状态分布')
            df4 = df.groupby(['engineerName'], as_index=False).agg('count').sort_values(by='taskHandOutStatus',ascending=False,inplace=False).iloc[:10]
            Pie(cols[1], df4, 'taskHandOutStatus', 'engineerName', '工程师分布')
            
            def getPartsDfmeaStats(df, groupBy):
                rs = []
                projStatus = {}
                tdf = df.groupby([groupBy, 'taskHandOutStatus'], as_index=False).agg('count')
                records = list(tdf.values)
                for record in records:
                    gp = record[0]
                    stat = record[1]
                    cnt = record[2]
                    pStats = [0,0,0,0,0,0]
                    if gp in projStatus:
                        pStats = projStatus[gp]
                    if stat == '已分析':
                        pStats[0] += cnt
                    elif stat == '分析中':
                        pStats[1] += cnt
                    elif stat == '未分析':
                        pStats[2] += cnt
                    sAll = pStats[0] + pStats[1] + pStats[2]
                    sCmp = pStats[0] + pStats[1]
                    pStats[3] = sAll
                    pStats[4] = sCmp
                    if sAll > 0:
                        pStats[5] = float(sCmp) / float(sAll)
                    projStatus[gp] = pStats
                for k in projStatus.keys():
                    v = projStatus[k]
                    #r1 = {groupBy:k, '已分析':v[0], '分析中':v[1], '未分析':v[2], '总数':v[3], '完成率':v[4]}
                    r1 = {groupBy:k, 'type':'已分析', 'value':v[4], 'rate':v[5]}
                    r2 = {groupBy:k, 'type':'总数', 'value':v[3], 'rate':v[5]}
                    #r3 = {groupBy:k, 'type':'完成率', 'value':v[4]}
                    rs.append(r1)
                    rs.append(r2)
                    #rs.append(r3)
                return rs

            rs = getPartsDfmeaStats(df, 'projectNo')
            pdf = pd.DataFrame(rs)
            rs = getPartsDfmeaStats(df, 'cocCode')
            cdf = pd.DataFrame(rs)

            col1, col2 = st.columns(2)
            pdf = pdf.sort_values(by=['rate','type'],ascending=[False, True],inplace=False)
            cdf = cdf.sort_values(by=['rate','type'],ascending=[False, True],inplace=False)
            Bar3(col1, pdf, 'projectNo', 'value', 'value','项目DFMEA分析状态', 'v', 400, 'group', 'type', 'rate')
            Bar3(col2, cdf, 'cocCode', 'value', 'value','部门DFMEA分析状态', 'v', 400, 'group', 'type', 'rate')   

            #tdf = df.groupby(['cocCode', 'taskHandOutStatus'], as_index=False).agg('count')
            #st.dataframe(tdf, use_container_width=True)

            #tdf = getProjectDfmeaRate()  
            #tdf
        ep = tab.expander('系统运行分析')
        with ep:
            if dfmeaSessionId:
                #tab.write('dfmeaSessionId : %s' % dfmeaSessionId)
                showApp()

                st.subheader('项目DFMEA')
                rs = getProjectDFMEAPageList()
                if rs:
                    df = pd.DataFrame(rs)
                    col1, col2, col3 = st.columns(3)
                    tdf = df
                    tdf = tdf.groupby(['部门'], as_index=False).agg('count')
                    tdf = tdf.sort_values(by='id',ascending=True,inplace=False).iloc[-20:]                
                    Bar2(col1, tdf, '部门', 'id', 'id','部门', 'v', 400)

                    tdf = df
                    tdf = tdf.groupby(['系统'], as_index=False).agg('count')
                    tdf = tdf.sort_values(by='id',ascending=True,inplace=False).iloc[-20:]                
                    Bar2(col2, tdf, '系统', 'id', 'id','系统', 'v', 400)

                    tdf = df
                    tdf = tdf.groupby(['创建者'], as_index=False).agg('count')
                    tdf = tdf.sort_values(by='id',ascending=True,inplace=False).iloc[-20:]                
                    Bar2(col3, tdf, '创建者', 'id', 'id','创建者', 'v', 400)

                    col1, col2, col3 = st.columns(3)
                    tdf = df
                    tdf = tdf.groupby(['项目'], as_index=False).agg('count')
                    tdf = tdf.sort_values(by='id',ascending=True,inplace=False).iloc[-20:]                
                    Bar2(col1, tdf, '项目', 'id', 'id','项目', 'v', 400)

                    tdf = df
                    tdf = tdf.groupby(['版本'], as_index=False).agg('count')
                    tdf = tdf.sort_values(by='id',ascending=True,inplace=False).iloc[-20:]                
                    Bar2(col2, tdf, '版本', 'id', 'id','版本', 'v', 400)

                st.subheader('家族DFMEA')
                rs = getMasterDFMEAPageList()
                if rs:
                    df = pd.DataFrame(rs)

                    col1, col2, col3 = st.columns(3)
                    tdf = df
                    tdf = tdf.groupby(['部门'], as_index=False).agg('count')
                    tdf = tdf.sort_values(by='id',ascending=True,inplace=False)#.iloc[-20:]                
                    Bar2(col1, tdf, '部门', 'id', 'id','部门', 'v', 400)

                    tdf = df
                    tdf = tdf.groupby(['创建者'], as_index=False).agg('count')
                    tdf = tdf.sort_values(by='id',ascending=True,inplace=False)#.iloc[-20:]                
                    Bar2(col2, tdf, '创建者', 'id', 'id','创建者', 'v', 400)

                    #tdf = df
                    #tdf = tdf.groupby(['系统'], as_index=False).agg('count')
                    #tdf = tdf.sort_values(by='id',ascending=True,inplace=False)#.iloc[-20:]                
                    #Bar2(col3, tdf, '系统', 'id', 'id','系统', 'v', 400)
            else:
                dfmeaLogin()
        
    elif sysName == 'PQ':
        def gradingScoreBar(df, group, container, title):
            tdf = df
            tdf = tdf.query('gradingScore > 1 and gradingScore <= 10').groupby([group], as_index=False).agg('mean')
            tdf['gradingScore'] = tdf.apply(lambda x:round(x['gradingScore']*100), axis=1)
            tdf = tdf.sort_values(by='gradingScore',ascending=True,inplace=False)
            Bar2(container, tdf, group, 'gradingScore', 'gradingScore',title, 'v', 400)
            return tdf
        
        def gradingScoreRedar(df, group, container, title, range):
            tdf = df
            tdf = tdf.query('gradingScore > 1 and gradingScore <= 10').groupby([group], as_index=False).agg('mean')
            tdf['gradingScore'] = tdf.apply(lambda x:round(x['gradingScore']*100), axis=1)
            Radar(container, tdf, title, 'gradingScore', group, range)

        def recordCountBar(df, group, container, title, bSort=False):
            tdf = df
            tdf = tdf.groupby([group], as_index=False).agg('count')
            if bSort: 
                tdf = tdf.sort_values(by='id',ascending=True,inplace=False)               
            Bar2(container, tdf, group, 'id', 'id', title, 'v', 400)
            return tdf
        
        def showPQOverview():
            dtNow, dtLast1, dtLast2, evCount1, evCount2, erCount1, erCount2, cmCount1, cmCount2, carModels1, carModels2 = getPQOverview() 

            col1, col2, col3, col4 = st.columns([3,3,3,9])
            col1.metric("月度评分数", evCount1, evCount1-evCount2)
            col2.metric("月度评分用户数", erCount1, erCount1-erCount2)
            col3.metric("月度评分车型数", cmCount1, cmCount1-cmCount2)
            col4.caption('评分车型 :N :blue[本月：**%s**] :N :blue[上月：**%s**]' % ('** ， **'.join(carModels1), '** ， **'.join(carModels2)))            
            qs = '''
            本月度 %s 至 %s 时间段内: 评分数量为%d个, 进行评分的工程师数量为%d人, 进行评分的车型数量为%d个, 进行评分的车型为：%s
            上个月度 %s 至 %s 时间段内: 评分数量为%d个, 进行评分的工程师数量为%d人, 进行评分的车型数量为%d个, 进行评分的车型为：%s
            ''' % (dtLast1, dtNow, evCount1, erCount1, cmCount1, carModels1, 
                    dtLast2, dtLast1, evCount2, erCount2, cmCount2, carModels2)
            q = '以资深数据分析师的身份对以下括号中的数据进行深度分析，给出月度分析报告和观点, 请用markdown语法输出内容, 请将重要或关键的内容用加粗红色字体表示出来 (%s)' % qs                
            nt = utc_now()
            #qk = 'pqOverview_%s_%s_%s' % (nt.year, nt.month, nt.day)
            qk = 'pqOverview'
            return qk, q

        def getDataframeString(df, useCols, indexKey):
            tdf = df
            ks = []
            for k in useCols:
                tdf[k] = tdf[useCols[k]]
                ks.append(k)
            tdf = tdf[ks]
            tdf = tdf.set_index(indexKey)
            ts = str(tdf.to_dict())
            return ts

        @st.cache_data()
        def showPQDashboard():
            rs = recordsDB.all()
            df = pd.DataFrame(rs)

            col1, col2 = st.columns(2)
            tdf = df.groupby(['evaluationYear', 'evaluationMonth'], as_index=False).agg('count')                
            tdf['ym'] = tdf.apply(lambda col: ym(col['evaluationYear'], col['evaluationMonth']), axis=1)
            Bar2(col1, tdf, 'ym', 'id', 'id', '月评分数', 'v', 400)
            s1 = getDataframeString(tdf, {'数量':'id', '月度':'ym'}, '月度')
            
            tdf = df.groupby(['evaluationYear', 'evaluationMonth', 'evaluationDay'], as_index=False).agg('count')              
            tdf['ymd'] = tdf.apply(lambda col: ymd(col['evaluationYear'], col['evaluationMonth'], col['evaluationDay']), axis=1)
            Bar2(col2, tdf, 'ymd', 'id', 'id','日评分数', 'v', 400)

            col1, col2, col3 = st.columns(3)
            tdf = recordCountBar(df, 'evaluatorName', col1, '用户评分数', True)
            s2 = getDataframeString(tdf, {'数量':'id', '评分人':'evaluatorName'}, '评分人')

            tdf = recordCountBar(df, 'pName1', col2, '一级维度评分数', True)
            s3 = getDataframeString(tdf, {'数量':'id', '一级评分维度':'pName1'}, '一级评分维度')

            tdf = df[['gradingScore', 'pName1']]
            tdf = tdf.query('gradingScore > 1 and gradingScore <= 10').groupby(['pName1'], as_index=False).agg('mean')
            tdf['gradingScore'] = tdf.apply(lambda x:round(x['gradingScore']*100), axis=1) 
            tdf = tdf.sort_values(by='gradingScore',ascending=True,inplace=False)#.iloc[-20:]                
            Bar2(col3, tdf, 'pName1', 'gradingScore', 'gradingScore','一级维度均分', 'v', 400)

            s4 = getDataframeString(tdf, {'数值':'gradingScore', '一级评分维度':'pName1'}, '一级评分维度')

            col1, col2, col3, col4 = st.columns(4)
            tdf = recordCountBar(df, 'evaluatorSex', col1, '性别评分数', True)
            s5 = getDataframeString(tdf, {'数量':'id', '性别':'evaluatorSex'}, '性别')

            tdf = recordCountBar(df, 'evaluatorAgeGroup', col2, '年龄段评分数', True)
            s6 = getDataframeString(tdf, {'数量':'id', '年龄段':'evaluatorAgeGroup'}, '年龄段')

            tdf = recordCountBar(df, 'evaluatorWeight', col3, '体重评分数')
            s7 = getDataframeString(tdf, {'数量':'id', '体重':'evaluatorWeight'}, '体重')

            tdf = recordCountBar(df, 'evaluatorHeight', col4, '身高评分数')
            s8 = getDataframeString(tdf, {'数量':'id', '身高':'evaluatorHeight'}, '身高')            

            col1, col2, col3, col4 = st.columns(4)
            tdf = gradingScoreBar(df, 'evaluatorSex', col1, '性别评分均分')
            s9 = getDataframeString(tdf, {'数值':'gradingScore', '性别':'evaluatorSex'}, '性别')

            tdf = gradingScoreBar(df, 'evaluatorAgeGroup', col2, '年龄段评分均分')
            s10 = getDataframeString(tdf, {'数值':'gradingScore', '年龄段':'evaluatorAgeGroup'}, '年龄段')

            tdf = gradingScoreBar(df, 'evaluatorWeight', col3, '体重评分均分')
            s11 = getDataframeString(tdf, {'数值':'gradingScore', '体重':'evaluatorWeight'}, '体重')

            tdf = gradingScoreBar(df, 'evaluatorHeight', col4, '身高评分均分')
            s12 = getDataframeString(tdf, {'数值':'gradingScore', '身高':'evaluatorHeight'}, '身高')

            
            col1, col2 = st.columns(2)
            tdf = recordCountBar(df, 'carModel', col1, '车型评分数', True)
            s13 = getDataframeString(tdf, {'数量':'id', '车型':'carModel'}, '车型')
            tdf = gradingScoreBar(df, 'carModel', col2, '车型评分均分')            
            s14 = getDataframeString(tdf, {'数值':'gradingScore', '车型':'carModel'}, '车型') 

            tdf = df
            tdf = tdf.query('gradingRecordingUrl == gradingRecordingUrl')
            tdf
            for url in tdf['gradingRecordingUrl'].values:
                st.audio(url, format='audio/3gpp')

            #pqUrl = 'https://digi.jetour.com.cn'
            #rs = recordsDB.search(~(recordsQuery.pictureList == []))
            #for r in rs:
            #    imgUrls = []
            #    pics = r['pictureList']
            #    for pic in pics:
            #        picUrl = pic['pictureUrl']
            #        if picUrl:
            #            imgUrls.append(pqUrl + pic['pictureUrl']) 
            #    if imgUrls:   
            #        st.image(imgUrls, width=200)           

            qs = '''月度评分次数：%s, 评分人的评分次数：%s, 一级维度评分次数：%s, 一级维度平均分：%s, 
            按评分人性别的评分次数：%s, 按评分人年龄段的评分次数：%s, 按评分人体重的评分次数：%s, 按评分人身高的评分次数：%s,
            按评分人性别的评分均分：%s, 按评分人年龄段的评分均分：%s, 按评分人体重的评分均分：%s, 按评分人身高的评分均分：%s,
            对车型的评分次数：%s, 对车型的评分均分：%s''' % (s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, s14)
            q = '以汽车研发设计行业数据分析师的身份对以下括号中对汽车的主观感官评价数据进行分析，该数据为汽车研发专业工程师评价并非来自用户，给出280字左右的数据分析和观点, 请用markdown语法输出内容, 用加粗红色字体将其中重要内容表示出来  (%s)' % qs
            nt = utc_now()
            #qk = 'pqDashboard_%s_%s_%s' % (nt.year, nt.month, nt.day)
            qk = 'pqDashboard'
            return qk, q
        
        @st.cache_data() 
        def showModelDashboard(model):
            rs = recordsDB.all()
            df = pd.DataFrame(rs)   

            df = df.query('carModel == "%s"' % model)

            col1, col2, col3 = st.columns(3)
            tdf = df
            tdf = tdf.query('gradingScore > 1 and gradingScore <= 10').groupby(['pName1'], as_index=False).agg('mean')
            tdf['gradingScore'] = tdf.apply(lambda x:round(x['gradingScore']*100), axis=1) 
            tdf = tdf.sort_values(by='gradingScore',ascending=True,inplace=False)#.iloc[-20:]                
            #Bar2(col1, tdf, 'pName1', 'gradingScore', 'gradingScore','一级维度均分', 'v', 400)
            gradingScoreRedar(df, 'pName1', col1, '一级维度平均分', [500, 800])
            recordCountBar(df, 'evaluatorName', col2, '用户评分数', True)
            recordCountBar(df, 'pName1', col3, '一级维度评分数', True)
            
            col1, col2 = st.columns(2)
            #gradingScoreBar(df, 'dimensionName', col1, '细分维度平均分') 
            gradingScoreRedar(df, 'dimensionName', col1, '细分维度平均分', [500, 800])
            recordCountBar(df, 'dimensionName', col2, '细分维度评分数', True)

            col1, col2, col3, col4 = st.columns(4)
            recordCountBar(df, 'evaluatorSex', col1, '性别评分数', True)
            recordCountBar(df, 'evaluatorAgeGroup', col2, '年龄段评分数', True)
            recordCountBar(df, 'evaluatorWeight', col3, '体重评分数')
            recordCountBar(df, 'evaluatorHeight', col4, '身高评分数')

            col1, col2, col3, col4 = st.columns(4)
            gradingScoreBar(df, 'evaluatorSex', col1, '性别评分均分')
            gradingScoreBar(df, 'evaluatorAgeGroup', col2, '年龄段评分均分')
            gradingScoreBar(df, 'evaluatorWeight', col3, '体重评分均分')
            gradingScoreBar(df, 'evaluatorHeight', col4, '身高评分均分')

            
                       

            #dims = {'视觉':'pName4','内心感受':'pName3','触觉':'pName4','听觉':'pName2','嗅觉':'pName4'}
            #for pName in dims.keys():
            #    tdf = df.query('pName1 == "%s"' % pName)
            #    col1, col2 = st.columns(2)
            #    dimName = dims[pName]
            #    recordCountBar(tdf, dimName, col1, '%s子维度评分数' % pName, True)
            #    gradingScoreBar(tdf, dimName, col2, '%s子维度均分' % pName)

        dimensions = ['驾乘视野', 'HMI', '乘坐空间', '做工精细化', '储物空间', '功能件操作&运行声品', '座椅&约束系统', '开关按键声品',
                  '开关按键操作手感', '提示&警示声品', '操作便利性', '材质质感', '灯光&背光', '美观性', '色彩&纹理', '车内气味', 
                  '门盖的开闭品质','饰件的握感&触感', '音响效果', '功能件操作手感']

        @st.cache_data() 
        def showModelDimensionDashboard(model, dimension):
            rs = recordsDB.all()
            df = pd.DataFrame(rs)    
            df = df.query('carModel == "%s" and dimensionName == "%s"' % (model, dimension))

            showColumns = {'pName1':'一级维度','pName2':'二级维度','pName3':'三级维度','pName4':'四级维度', 'name':'评分项', 'gradingScore':'评分', 'evaluatorName':'评分人', 'evaluationTime':'评分时间'}
            df = df[showColumns.keys()]
            tdf = df.copy()     
            tdf = tdf.rename(columns=showColumns)#.set_index('一级维度')
            st.dataframe(tdf, use_container_width=True)

        with tab.expander('系统运行指标'):
            tab1, tab2 = st.tabs(['指标','分析'])
            qk=q=''
            with tab1:
                qk, q = showPQOverview()
            with tab2:
                getOrAskGPT(qk, q) 

        with tab.expander('总体分析'):
            tab1, tab2 = st.tabs(['指标','分析'])
            qk=q=''
            with tab1:
                qk, q = showPQDashboard()
            with tab2:
                getOrAskGPT(qk, q)

        with tab.expander('车型分析'):
            rs = recordsDB.all()
            df = pd.DataFrame(rs)
            df = df.groupby(['carModel'], as_index=False).agg('count')
            models = list(df['carModel'])
            model = st.selectbox('请选择评分车型', models)
            showModelDashboard(model)

            dimension = st.selectbox('选择细分维度', dimensions)
            showModelDimensionDashboard(model, dimension)

        def pqFakeDashboard():
            tab.image("https://digi.jetour.com.cn/pq-admin/admin/sys-file/jetour-self-sit?fileName=public/cjtcloud/b4e9bc82987c4502bd17b90544e77e23.jpg", width=200)
            tab.markdown(':red[PQ系统介绍]')
            uploader = tab.file_uploader('选择一个PQ评分计划')
            if uploader is not None:
                f = pd.ExcelFile(uploader)
                pqData = pd.read_excel(uploader)
                tab.dataframe(pqData)
            tab.header('PQ评分计划')
            uploader = tab.file_uploader('选择一个PQ评分表')
            if uploader is not None:
                f = pd.ExcelFile(uploader)
                sheetNames = f.sheet_names
                pqData = pd.read_excel(uploader, sheet_name=sheetNames, skiprows=2, header=[0])            
                for sheetName in sheetNames:
                    vIdx = 6
                    if sheetName == '内心感受':
                        vIdx = 5
                    rows = pqData[sheetName].values
                    cats = {}
                    for row in rows:
                        c2 = row[1]
                        v2 = float(row[vIdx])
                        if v2 > 1:
                            if c2 in cats:   
                                cats[c2].append(v2)
                            else:
                                cats[c2] = [v2]
                    data = []
                    for key in cats.keys():
                        vs = cats[key]                     
                        av = average(vs)
                        data.append({'s':key, 'v':av})
                    tab.write(data)
                    if len(data) > 0:
                        Radar(tab,data, sheetName,'v','s', [0,10])
                    else:
                        tab.write('无评分数据')

                    if sheetName == '视觉' or sheetName == '触觉':
                        cats = {}
                        for row in rows:
                            c2 = row[3]
                            v2 = float(row[vIdx])
                            if v2 > 1:
                                if c2 in cats:   
                                    cats[c2].append(v2)
                                else:
                                    cats[c2] = [v2]
                        data2 = []
                        for key in cats.keys():
                            vs = cats[key]                     
                            av = average(vs)
                            data2.append({'s':key, 'v':av})
                        Radar(tab,data2, sheetName,'v','s', [0,10])    

                    
                    if True:#sheetName == '视觉':
                        n = len(data)
                        cn = 4
                        cols = tab.columns(cn)
                        i = 0
                        for d in data:
                            k = d['s']
                            subCats = {}
                            for row in rows:
                                c2 = row[1]
                                if k == c2:
                                    c3 = row[2]
                                    v2 = float(row[vIdx])
                                    if v2 > 1:
                                        if c2 in subCats:   
                                            subCats[c3].append(v2)
                                        else:
                                            subCats[c3] = [v2]
                            data = []
                            for key in subCats.keys():
                                vs = subCats[key]                     
                                av = average(vs)
                                data.append({'s':key, 'v':av})
                            Radar(cols[i % cn],data, k,'v','s', [0,10])
                            i = i + 1
                            
                
        
    elif sysName == 'BOM':
        ep = tab.expander('加载BOM数据文件')
        uploader = ep.file_uploader('选择一个BOM数据文件')
        if uploader is not None:
            data = pd.read_excel(uploader)
            bomArray = data.values
            N = 20#len(bomArray)
            rootData = [0, '', 0, 'ROOT', 'BOM ROOT', 'RRR', 1, '1Y', '', '', '', 'ROOT', '', '', '', '', '', '', '']
            bomLines = [rootData]
            for i in range(8, N):
                bomLine = [i-7]
                for d in bomArray[i]:
                    bomLine.append(d)
                bomLines.append(bomLine)         
        
            lastTreeNodes = {0:rootData}
            treeDatas = []    
            def solveTreeData(treeData):
                for data in treeData:
                    levelStr = str(data[7])
                    isNode = False
                    level = 0
                    leafData = {}
                    lData = [data[0], data[3], data[7]]
                    v = '零件号：'+str(data[3])+'<br>零件名称：'+str(data[4])+'<br>英文名称：'+str(data[5])+'<br>负责部门：'+str(data[1])+'<br>负责人员：'+str(data[11])+'<br>CMAN：'+str(data[-1])
                    if 'Y' in levelStr:
                        isNode = True
                        level = int(levelStr.split('Y')[0])
                        lastTreeNodes[level] = lData
                        leafData = {'id':data[0], 'name':data[4], 'parent':lastTreeNodes[level-1][0], 'data':lData, 'value':v}            
                    else:
                        level = int(levelStr)
                        leafData = {'id':data[0], 'name':data[4], 'parent':lastTreeNodes[level][0], 'data':lData, 'value':v}
                    treeDatas.append(leafData) 
                    #ep.write(leafData)
            solveTreeData(bomLines)
            def generate_tree(source, parent, cache=[]):
                tree = []
                for item in source:
                    id = item["id"]
                    if id in cache:
                        continue
                    if item["parent"] == parent:
                        cache.append(id)
                        item["children"] = generate_tree(source, id, cache)
                        tree.append(item)
                return tree            
            bTreeData = generate_tree(treeDatas, 0)
            
            ep.write(bTreeData)
    elif sysName == 'DFMEA2.0':
        @st.cache_data()
        def loadCPACSheet():
            df = pd.read_excel('奇瑞产品架构分组清单-20220825.xlsx', header=1)
            df = df.query('CPAC描述 == CPAC描述')
            df['CPAC编码'] = df.apply(lambda col: str(col['CPAC编码']), axis=1) 
            tdf = df[['CPAC编码','CPAC描述']]
            tdf
            
        with tab:
            loadCPACSheet()
    elif sysName == 'ALM':
        import plotly.graph_objects as go
        from datetime import datetime
        tab.title("项目管理甘特图")
        data = [
            {"项目名称": "项目A", "阶段": "需求分析", "责任人": "张三", "计划开始日期": datetime(2022, 1, 1), "计划结束日期": datetime(2022, 1, 15), "实际开始日期": datetime(2022, 1, 3), "实际结束日期": datetime(2022, 1, 18), "风险点": "无"},
            {"项目名称": "项目A", "阶段": "设计", "责任人": "李四", "计划开始日期": datetime(2022, 1, 15), "计划结束日期": datetime(2022, 2, 15), "实际开始日期": datetime(2022, 1, 18), "实际结束日期": datetime(2022, 2, 20), "风险点": "设计变更"},
            {"项目名称": "项目A", "阶段": "开发", "责任人": "王五", "计划开始日期": datetime(2022, 2, 15), "计划结束日期": datetime(2022, 3, 31), "实际开始日期": datetime(2022, 2, 20), "实际结束日期": datetime(2022, 4, 10), "风险点": "代码质量"},
            {"项目名称": "项目A", "阶段": "测试", "责任人": "赵六", "计划开始日期": datetime(2022, 3, 31), "计划结束日期": datetime(2022, 4, 30), "实际开始日期": datetime(2022, 4, 10), "实际结束日期": datetime(2022, 5, 5), "风险点": "测试用例不全"},
            {"项目名称": "项目A", "阶段": "上线", "责任人": "田七", "计划开始日期": datetime(2022, 4, 30), "计划结束日期": datetime(2022, 5, 15), "实际开始日期": datetime(2022, 5, 5), "实际结束日期": datetime(2022, 5, 18), "风险点": "上线出现问题"}
        ]
        fig = go.Figure()
        for i, d in enumerate(data):
            fig.add_trace(go.Bar(
                x=[d["责任人"], d["责任人"]],
                y=[d["计划开始日期"], d["计划结束日期"]],
                base=d["计划开始日期"],
                orientation='h',
                marker=dict(
                color='rgba(0, 0, 255, 0.7)',
                line=dict(color='rgba(0, 0, 255, 1.0)', width=1)
                ),
                name=d["阶段"],
                hovertemplate="阶段: %{name}计划开始日期: %{base}计划结束日期: %{y}责任人: %{x}实际开始日期: %{customdata[0]}实际结束日期: %{customdata[1]}风险点: %{customdata[2]}",
                customdata=[[d["实际开始日期"], d["实际结束日期"], d["风险点"]]],hoverinfo="name+x+y+text"))
            fig.update_layout(
                title="项目A甘特图",
                xaxis=dict(title="责任人"),
                yaxis=dict(title="日期"),
                hovermode="closest",
                height=800)
            tab.plotly_chart(fig)

    elif sysName == '已建系统数据':
        tab.write('AAA')

    elif sysName == 'GPT':
        st.markdown('<style>div.Widget.row-widget.stTextbox {width: 800px}</style>', unsafe_allow_html=True)
        with tab:
                #q = st.text_area('请输入您的问题','请解析下列三重引号内的文本内容，将形如"人名(昵称) "，去掉括号和昵称，只列出人名列表，用分号分割该列表')
                q = st.text_area('请输入您的问题')
                if st.button('回答'):
                    r = askGPT('q', q, 0.8)

if s == '已建系统':
    st.header('已建信息化系统运行分析报告')
    sysPages(deps)
elif s == '在建系统':
    st.header('在建信息化系统建设进展报告')
    sysPages(devs)
elif s == '其他':
    sysPages(cfgs)
