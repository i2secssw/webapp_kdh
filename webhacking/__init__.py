#_*_ coding: utf-8 _*_
from flask import Flask, render_template, redirect, send_from_directory, request, make_response, session, escape, render_template_string, send_file
import sys, unicodedata, os, time
import mysql.connector
import hashlib
from mysql.connector.errors import Error

app = Flask(__name__)
app.secret_key = 'a'

host ='localhost'
data_base = 'webhacking'
user ='root'
password = '1234'


@app.route('/')
def index(): 
    if request.cookies.get('Level') != '0' and request.cookies.get('Id') != "" and request.cookies.get('Level') != None and request.cookies.get('Id') != None:
        return redirect('/main')
    else:
        resp = make_response(render_template('index.html'))
        resp.set_cookie('Id', "")
        resp.set_cookie('Level', '0')
        return resp


@app.route('/main')
def main():
    if 'userId' in session:
        return redirect('/main/list')
    
    if  request.cookies.get('Id') == None:
        return redirect('/') 

    session['userId'] = request.cookies.get('Id')
    return "<script>alert('%s님 환영합니다.'); window.location='/main/list';</script>" % str(session['userId'])


@app.route('/main/list',methods=['GET','POST'])
#기본적으로 get방식이고, search일 때는 post 방식 post일 때를 위로 해서 search(제목) 할 때 그에 해당하는 게시글만 select해서 출력하게
#취약한 쿼리문은 select * board where bbs_title='' order by bbs_no desc

def main_list():
    if request.cookies.get('Level') == '2' and request.cookies.get('Id') != 'admin':
        Id = 'admin' 
        session['userId'] = Id
        resp = make_response(redirect('/main'))
        resp.set_cookie('Id',Id)
        return resp

    if request.method == 'POST':
        keyword = request.form['keyword']
        column = request.form['column']
        try:
            conn = mysql.connector.connect(user=user, password=password, host=host, database=data_base)
            cursor = conn.cursor()

            if str(column) == 'bbs_title':            
                sql_str = "select * from board where bbs_title = '%s' order by bbs_no desc" % (keyword)
                
            if str(column) == 'bbs_content':        
                sql_str = "select * from board where bbs_content = '%s' order by bbs_no desc" % (keyword)

            cursor.execute(sql_str)
            result = [] 
            rows = cursor.fetchall()

            if rows:
                result = list(rows)
                for i in range(0,len(result)):
                    if type(i) != int:
                        result[i] = ''.join(result[i])
                        result[i] = unicodedata.normalize('NFKD',result[i]).encode('ascii','ignore')
            return render_template('/board/list.html', userId=session['userId'], list=result, searchkeyword=keyword)
        except mysql.connector.Error as err:
            
            return err.msg
            
    
    if request.method == 'GET':
        conn = mysql.connector.connect(user=user, password=password, host=host, database=data_base)
        cursor = conn.cursor()      
        sql_str = "select * from board order by bbs_no desc"
        cursor.execute(sql_str)
        result = [] 
        rows = cursor.fetchall()

        if rows:
            result = list(rows)
            for i in range(0,len(result)):
                if type(i) != int:
                    result[i] = ''.join(result[i])
                    result[i] = unicodedata.normalize('NFKD',result[i]).encode('ascii','ignore')
        return render_template('/board/list.html', userId=session['userId'], list=result)


@app.route('/main/view',methods=['GET'])
def main_view():

    if request.method == 'GET':
        bbs_no = request.args.get('bbs_no')
        conn = mysql.connector.connect(user=user, password=password, host=host, database=data_base)
        cursor = conn.cursor()      
        #sql_str = "select * from board where bbs_no = '%s'" % bbs_no
        sql_str = "select * from board where bbs_no = %s" % bbs_no
        cursor.execute(sql_str)
        result = [] 
        rows = cursor.fetchone()

        if rows:
            sql_str = "update board set bbs_count = bbs_count+1 where bbs_no=%s" % (bbs_no)
            cursor.execute(sql_str)
            conn.commit()
            result = list(rows)

        return """
            <html>
            <div class="container" align='center'>
                    <h1>게시글 내용</h1>
                <form name="bbs_view" method="" action="" onsubmit="" >

                    <table  align='center' border='1'> 
                        <tr>
                            <td>작성자</td>
                            <td><textarea name='bbs_title' rows="1" cols="120" maxlength='40' readonly>%s</textarea></td>
                        </tr>
                        <tr>
                            <td>제 목</td>
                            <td>%s</td>
                            <!--<td><textarea name='bbs_content' rows ="20" cols="120" readonly>/textarea></td>-->
                        </tr>
                        <tr>
                            <td>내 용</td>
                            <td>%s</td>
                            <!--<td><textarea name='bbs_content' rows ="20" cols="120" readonly></textarea></td>-->
                        </tr>
                        <tr>
                            <td colspan="2">
                            <div align="center">
                            <input type="button" value="목록" onclick="location.href='/'"></div>
                            <!--<input type="submit" value="수정" >&nbsp;&nbsp;-->
                            <!--<input type="submit" value="삭제" >&nbsp;&nbsp;-->
                            </div>
                            </td>
                        </tr> 
                    </table>
                
                </form> 
            </div>
            </html>
        """ % (result[3].encode('utf-8'),result[1].encode('utf-8'),result[2].encode('utf-8'))


@app.route('/hi/')
def hi():
    if request.args.get('name'):
        name = request.args.get('name')
        template = '''<h2>Hello %s</h2>''' % name
    return render_template_string(template)


@app.route('/main/write')
def main_write():
    return render_template('/board/write.html')


@app.route('/write_chk',methods=['POST'])
def write_chk():
    now = time.localtime()
    bbs_title   = request.form['bbs_title']
    bbs_content = request.form['bbs_content']
    bbs_writer  = request.form['bbs_writer']
    bbs_date = "%04d-%02d-%02d %02d:%02d:%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
    bbs_count = 1
    secret_status = 'n'
    bbs_pass = request.form['bbs_pass']

    if bbs_pass != "":
        secret_status = 'y'

    conn = mysql.connector.connect(user=user, password=password, host=host, database=data_base, use_unicode=True, charset="utf8")
    cursor = conn.cursor()
    data = (bbs_title, bbs_content, bbs_writer, bbs_date, bbs_count, secret_status, bbs_pass)    
    sql_str = "insert into board values('', %s, %s, %s, %s, %s, %s, %s)"
    cursor.execute(sql_str,data)
    conn.commit()
    cursor.close()
    conn.close()
    return "<script>alert('작성한 게시글이 등록되었습니다.'); window.location='/';</script>"


@app.route('/main/revision')
def main_revision():
    return render_template('/board/revision.html')


@app.route('/main/delete')
def main_delete():
    return render_template('delete.html')#삭제하고 / 또는 list로 이동하게


@app.route('/admin', methods=['GET'])
def admin():
   
    
    if request.args.get('name'):
        admin_md5 = hashlib.md5('admin').hexdigest()
        if admin_md5 == request.args.get('name'):
            return send_from_directory('admin','index.html')
        else:
            return "<script>alert('잘못된 접근입니다.'); window.location='/';</script>"
    else:
        return "<script>alert('잘못된 접근입니다.'); window.location='/';</script>"


@app.route('/signup')
def signup():
    return render_template('/user/signup.html')


@app.route('/signup_chk',methods=['POST'])
def signup_chk():
    if request.method == "POST":
        conn = mysql.connector.connect(user=user, password=password, host=host, database=data_base, use_unicode=True, charset="utf8")
        cursor = conn.cursor()
        user_name = request.form['user_name']
        user_id = request.form['user_id']
        
        sql_str="select user_id from member where user_id='%s'" % (user_id)
        cursor.execute(sql_str)
        rows = cursor.fetchone()
        
        if rows > 0:
            return "<script>alert('이미 사용하고 있는 아이디입니다.'); window.location='/signup';</script>"
        
        user_pass = request.form['user_pass']
        user_registration_number = request.form['user_registration_number']
        user_birth_year = request.form['user_birth_year']
        user_birth_month = request.form['user_birth_month']
        user_birth_day = request.form['user_birth_day']
        user_addr = request.form['user_addr']
        user_mail = request.form['user_mail']
        
        data = (user_name, user_id, user_pass, user_registration_number, user_birth_year, user_birth_month, user_birth_day, user_addr, user_mail)
        sql_str = "insert into member values('', %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(sql_str,data)
        conn.commit()
        cursor.close()
        conn.close()
        return "<script>alert('회원가입이 정상적으로 이루어졌습니다.'); window.location='/';</script>"


@app.route('/login_chk',methods=['GET','POST'])
def login_chk():
    if request.method == "POST":
        conn = mysql.connector.connect(user=user, password=password, host=host, database=data_base)
        cursor = conn.cursor()
        user_id = request.form['user_id']
        user_pass = request.form['user_pass']      
        sql_str="select * from member where user_id='%s' and user_pass='%s'" % (user_id, user_pass)
        cursor.execute(sql_str)
        result = [] 
        rows = cursor.fetchall()
        if rows:
            result = list(rows[0])

            for i in range(2,len(result)):
                result[i] = ''.join(result[i])
                result[i] = unicodedata.normalize('NFKD',result[i]).encode('ascii','ignore')

                cursor.close()
                conn.close()
                resp = make_response(redirect('/'))
                resp.set_cookie('Id', result[2])
                if result[2] == 'admin':
                    resp.set_cookie('Level','2')
                else:
                    resp.set_cookie('Level', '1')
                return resp
                             
        else:
            app.logger.info("Not Mached!! ID or PW Check Please !!")
            return "<script>alert('잘못된 로그인입니다. 확인 후 다시 시도해 주십시오.'); window.location='/';</script>"
        
        cursor.close()
        conn.close()


@app.route('/myinfo_revision') #회원정보 수정(비밀번호, 비밀번호 확인, 주소, 이메일 )
def myinfo_revision():
    conn = mysql.connector.connect(user=user, password=password, host=host, database=data_base)
    cursor = conn.cursor()
    sql_str="select * from member where user_id='%s'" % (session['userId'])
    cursor.execute(sql_str)
    rows = cursor.fetchall()
    if rows:
        result = list(rows[0])

        for i in range(2,len(result)): # index 0 number, 1이름(한글), 8주소(한글)
            if i == 8:   
                continue
            result[i] = ''.join(result[i])
            result[i] = unicodedata.normalize('NFKD',result[i]).encode('ascii','ignore')

    user_name = result[1]
    user_id = result[2]
    user_registration_number = result[4]
    user_birth_year = result[5]
    user_birth_month = result[6]
    user_birth_day = result[7]
    user_addr = result[8]
    user_mail = result[9]

    return render_template('/user/myinfo_revision.html', user_id = user_id, user_name = user_name, user_registration_number = user_registration_number, user_birth_year = user_birth_year, user_birth_month = user_birth_month, user_birth_day = user_birth_day, user_addr = user_addr, user_mail = user_mail)


@app.route('/myinfo_revision_chk',methods=['POST'])
def myinfo_revision_chk():
    if request.method == "POST":
        conn = mysql.connector.connect(user=user, password=password, host=host, database=data_base, use_unicode=True, charset="utf8")
        cursor = conn.cursor()
        user_id = request.form['user_id']
        user_pass = request.form['user_pass']
        user_addr = request.form['user_addr']
        data = (user_pass, user_addr, user_id)
        sql_str = "update member set user_pass=%s, user_addr=%s where user_id=%s"
        cursor.execute(sql_str,data)
        conn.commit()
        cursor.close()
        conn.close()
    
    return "<script>alert('회원정보가 정상적으로 변경되었습니다.'); window.location='/';</script>"


@app.route('/logout')
def logout():
    resp = make_response(redirect('/'))
    resp.set_cookie('Id', "", expires=0)
    resp.set_cookie('Level',"", expires=0)
    session.pop('userId')
    return resp


#################### jinja2  template-injection
@app.route('/hello-template-injection')
def hello_ssti():
    person = {'name':"world", 'secret':"UGhldmJoZj8gYWl2ZnZoei5wYnovcG5lcnJlZg=="}
    if request.args.get('name'):
        person['name'] = request.args.get('name')
    template = '''<h2>Hello %s!</h2>''' % person['name']
    return render_template_string(template, person=person)

####
# Private function if the user has local files.
###
def get_user_file(f_name):
    with open(f_name) as f:
        return f.readlines()

app.jinja_env.globals['get_user_file'] = get_user_file # Allows for use in Jinja2 templates

if __name__ == "__main__":
    app.run(host='0.0.0.0',debug='True')