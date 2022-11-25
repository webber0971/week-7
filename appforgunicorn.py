from mysql.connector import pooling
import json
mydbPool=pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=3,
    host="localhost",
    user="root",
    password="123456789",
    database="WEBSITE"
)
print("成功連接到資料庫")
# 初始化伺服器
from flask import *
app=Flask(
    __name__,
    static_folder="public",
    static_url_path="/"
)
app.secret_key="secretKey"

# 處理路由
@app.route("/")
def index():
    return render_template("index.html")

# 進入會員頁
@app.route("/member")
def member():
    if "nickname" in session:
        nickname=session["nickname"]
        if nickname!="":
            nickname=nickname+"，"
        return render_template("/member.html",nic=nickname)
    else:
        return redirect("/")

# 回應前端對於留言的資料請求,從資料庫取得資料後先轉成json格式，方便前端處理
@app.route("/resultContentRequest")
def resultContentRequest():
    connector=mydbPool.get_connection()
    mycursor=connector.cursor()
    sql="SELECT NAME , content FROM MEMBER INNER JOIN MESSAGE ON MEMBER.ID=MESSAGE.MEMBER_ID order by time DESC"
    mycursor.execute(sql)
    allContent=mycursor.fetchall()
    mycursor.close()
    connector.close()
    jsonStr=json.dumps(allContent)
    jsonStr=str(jsonStr)
    return jsonStr

# /error?msg=錯誤訊息
@app.route("/error")
def error():
    message=request.args.get("msg","發生錯誤，請聯繫克服")
    return render_template("error.html",msa=message)

# 進入註冊頁面
@app.route("/register")
def register():
    return render_template("register.html")

# 註冊帳號 - 與資料庫互動
@app.route("/signup",methods=["POST"])
def signup():
    nickname=request.form["nickname"]
    email=request.form["email"]
    password=request.form["password"]
    connector=mydbPool.get_connection()
    mycursor=connector.cursor()
    sql="SELECT * FROM MEMBER WHERE EMAIL = %s"
    mycursor.execute(sql,(email,))
    nicknameResult=mycursor.fetchone()
    print(nicknameResult)
    if(nicknameResult != None):
        return redirect("/error?msg=信箱已經被註冊")
    sql="INSERT INTO MEMBER(NAME,EMAIL,PASSWORD) VALUES (%s,%s,%s)"
    val = (nickname,email,password)
    mycursor.execute(sql,val)
    connector.commit()
    mycursor.close()
    connector.close()
    return redirect("/")


# 登入 - 確認帳號密碼
@app.route("/signin",methods=["POST"])
def signin():
    passwordIndex=3
    email=request.form["email"]
    password=request.form["password"]
    connector=mydbPool.get_connection()
    mycursor=connector.cursor()
    sql="SELECT * FROM MEMBER WHERE EMAIL = %s"
    mycursor.execute(sql,(email,))
    clientGet=mycursor.fetchone()
    mycursor.close()
    connector.close()
    print(clientGet)
    if(clientGet==None):
        return redirect("/error?msg=帳號或密碼輸入錯誤")
    if(clientGet != None):
        if(clientGet[passwordIndex]!=password):
            return redirect("/error?msg=帳號或密碼輸入錯誤2")
    session["nickname"]=clientGet[1]
    session["id"]=clientGet[0]
    return redirect("/member")

# 登出 - 清除session資料
@app.route("/signout")
def signout():
    del session["nickname"]
    return redirect("/")

# 建立後端查詢會員資料的api
@app.get("/api/member")
def apiGetMemberData():
    userName=request.args.get("username","")
    connector=mydbPool.get_connection()
    mycursor=connector.cursor()
    sql = "select id,name,email from MEMBER where email = %s"
    mycursor.execute(sql,(userName,))
    memberData=mycursor.fetchone()
    mycursor.close()
    connector.close()#使用完後將連接放回連接池
    if(memberData==None):
        jsonStr={"data":None}
        return jsonStr
    jsonStr={"data":{"id" : memberData[0] ,"name" : memberData[1],"email": memberData[2]}}
    jsonStr=json.dumps(jsonStr)
    print(jsonStr)
    return str(jsonStr)

# 更改姓名
@app.patch("/api/member")
def postMemberName():
    if "nickname" in session:
        newName = request.json["newName"]
        idNumber=session["id"]
        try:
            connector=mydbPool.get_connection()
            mycursor=connector.cursor()
            sql="update MEMBER set name=%s where id=%s"
            val = (newName,idNumber)
            mycursor.execute(sql,val)
            connector.commit()
            mycursor.close()
            connector.close()
            print("更改完成")
            responseBody={"ok":True}
            session["nickname"]=newName
            return responseBody
        except:
            responseBody={"error":True}
            return responseBody
    else:
        responseBody={"error":True}
        return responseBody
app.run()