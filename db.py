from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.listview import ListItemButton,ListView
from kivy.adapters.listadapter import ListAdapter
import numpy as np
import mysql.connector

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  passwd="",
  database="dbp"
)
mycursor = mydb.cursor()

def login(username , password):
    cmd = 'select accountType, id from user where username = %s and password = %s'
    mycursor.execute(cmd ,(username,password))
    l = []
    for x in mycursor:
        l.append(x[0])
        l.append(x[1])
    if(len(l) == 0):
	    return -1
    
    return l

def hasNumbers(inputString):
	return any(char.isdigit() for char in inputString)

def hasAlpha(inputString):
	return any(char.isalpha() for char in inputString)

def add_new_user(username, email, password,difQID,difQans,accountType, bio='my bio is empty', photopath='~/1.png'):
	cmd = 'select * from  user where email = %s or username = %s'
	mycursor.execute(cmd ,(email,username))
	mycursor.fetchall()
	if(mycursor.rowcount != 0):
		return False
	if(len(password) < 8 or hasNumbers(password) == False or hasAlpha(password) == False):
		return False
	try:

		newcmd = 'insert into user(username, email, password, bio, photoPath, difQID,difQans,accountType , dtime) values (%s , %s , %s , %s , %s , %s ,%s,%s , (select NOW()))'
		mycursor.execute(newcmd , (username, email, password, bio,photopath,difQID,difQans,accountType))
		mydb.commit()
		return True
	except :
		return False

def get_dif_qs():
    cmd = 'select text , id from  difquestions'
    mycursor.execute(cmd )
    l = []
    for x in mycursor:
        l.append( (x[0] , x[1]))
    return l

def hasUser(username):
    cmd = 'select * from user where username = %s'
    mycursor.execute(cmd ,(username,))
    mycursor.fetchall()
    if(mycursor.rowcount == 0):
    	return False
    return True

def get_dif_q(username):
    try:
        cmd = 'select Q.text from difquestions as Q , user as U where U.username = %s and U.difQID = Q.id'
        mycursor.execute(cmd ,(username,))
        l = []
        for x in mycursor:
            l.append(x[0])
        return l[0]
    except:
        return False

def change_pass(username , newpass , qans):
    if(len(newpass) < 8 or hasNumbers(newpass) == False or hasAlpha(newpass) == False):
	    return False
    try:

        cmd = 'select * from user where username = %s and difQans = %s'
        mycursor.execute(cmd ,(username,qans))
        mycursor.fetchall()
        if(mycursor.rowcount == 0):
            return False
        cmd = 'update user set password = %s where username = %s and difQans = %s'
        mycursor.execute(cmd ,(newpass,username,qans))
        mydb.commit()
        return True
    except:
        return False

def tweet(posterID , postText, hashtaghs):
	if(len(hashtaghs) < 2):
		return False
	cmd = 'select * from post where text = %s and posterID = %s and id in(select T.id from tweet as T)'
	mycursor.execute(cmd ,(postText,posterID))
	mycursor.fetchall()
	if(mycursor.rowcount != 0):
		return False
	# print('here')
	try:
		newcmd = 'insert into post(text, posterID, dtime) values (%s , %s ,(select NOW()) )'
		mycursor.execute(newcmd , (postText,posterID))
		newcmd = 'insert into tweet(id) values ((select id from post where posterID = %s and text = %s))'
		mycursor.execute(newcmd , (posterID,postText))
			
		for i in hashtaghs:
			newcmd = 'insert into hashtag(tweet_id , text) values ((select id from post where posterID = %s and text = %s) , %s)'
			mycursor.execute(newcmd , (posterID,postText , i))
		mydb.commit()
		return True
	except:
		return False

def get_last_hdposts(userID):
	cmd = 'select P.text, P.id from post as P, tweet as T where T.id = P.id and P.posterID in (select M.followedID from follow as M where M.followerID = %s) order by dtime desc limit 100'
	mycursor.execute(cmd , (userID,))
	l = []
	for x in mycursor:
  		l.append( (x[0] , x[1]))
	return l

def get_comments(postID):
    cmd = 'select P.text , P.id from post as P , comment as C where C.id = P.id and C.tweet_id = %s and C.rep_id is NULL'
    mycursor.execute(cmd , (postID,))
    l = []
    for x in mycursor:
    	l.append( (x[0] , x[1]))
    return l

def get_user_id(postId):
    cmd = 'select posterID from post where id=  %s '
    mycursor.execute(cmd , (postId,))
    l = []
    for x in mycursor:
    	l.append( x[0] )
    return l[0]

def get_reps(commentId):
    cmd = 'select P.text , P.id from post as P , comment as C where C.id = P.id and C.rep_id  = %s and C.tweet_id = (select Y.tweet_id from comment as Y where Y.id = %s)'
    mycursor.execute(cmd , (commentId,commentId))
    l = []
    for x in mycursor:
    	l.append( (x[0] , x[1]))
    return l
    
def get_user_posts(userId):
    cmd = 'select P.text , P.id from post as P, tweet as T  where T.id = P.id and P.posterID = %s order by P.dtime desc'
    # print(userId)
    mycursor.execute(cmd , (userId,))
    l = []
    for x in mycursor:
    	l.append( (x[0] , x[1]))
    return l

def comment(userId , postId , commentText):
    cmd = 'select * from tweet where id = %s'
    mycursor.execute(cmd ,(postId,))
    mycursor.fetchall()
    if(mycursor.rowcount != 0):
        newcmd = 'insert into post(text, posterID, dtime) values (%s , %s ,(select NOW()) )'
        mycursor.execute(newcmd , (commentText,userId))
        newcmd = 'insert into comment(id , tweet_id) values ((select id from post where posterID = %s and text = %s order by id desc limit 1) , %s)'
        mycursor.execute(newcmd , (userId,commentText,postId))
        mydb.commit()
        return True
    else:
        cmd = 'select rep_id from comment where id = %s'
        mycursor.execute(cmd ,(postId,))
        l = []
        for x in mycursor:
            l.append( x[0])
        l = l[0]
        if l == None:
            newcmd = 'insert into post(text, posterID, dtime) values (%s , %s ,(select NOW()) )'
            mycursor.execute(newcmd , (commentText,userId))
            r = 'select tweet_id from comment where id = %s'
            mycursor.execute(r , (postId,))
            q = []
            for x in mycursor:
                q.append( x[0])
            q = q[0]
            newcmd = 'insert into comment(id , tweet_id, rep_id) values ((select id from post where posterID = %s and text = %s order by id desc limit 1) , %s , %s)'
            mycursor.execute(newcmd , (userId,commentText,q,postId))
            mydb.commit()
            return True
        else:
            cmd = 'select rep_id from comment where id = %s'
            mycursor.execute(cmd ,(l,))
            l = []
            for x in mycursor:
                l.append( x[0])
            l = l[0]
            if l == None:
                newcmd = 'insert into post(text, posterID, dtime) values (%s , %s ,(select NOW()) )'
                mycursor.execute(newcmd , (commentText,userId))
                r = 'select tweet_id from comment where id = %s'
                mycursor.execute(r , (postId,))
                q = []
                for x in mycursor:
                    q.append( x[0])
                q = q[0]
                newcmd = 'insert into comment(id , tweet_id, rep_id) values ((select id from post where posterID = %s and text = %s order by id desc limit 1) , %s , %s)'
                mycursor.execute(newcmd , (userId,commentText,q,postId))
                mydb.commit()
                return True
    return False

def like(postID, userID):
	cmd = 'select * from  likes where postID = %s and userID = %s'
	mycursor.execute(cmd ,(postID,userID))
	mycursor.fetchall()
	if(mycursor.rowcount != 0):
		return False
	try :
		newcmd = 'insert into likes(postID, userID) values (%s , %s )'
		mycursor.execute(newcmd , (postID , userID))
		mydb.commit()
		return True
	except:
		return False

def unlike(postID, userID):
	cmd = 'select * from  likes where postID = %s and userID = %s'
	mycursor.execute(cmd ,(postID,userID))
	mycursor.fetchall()
	if(mycursor.rowcount == 0):
		return False
	try:
		newcmd = 'delete from likes where postID = %s and userID = %s'
		mycursor.execute(newcmd , (postID , userID))
		mydb.commit()
		return True
	except:
		return False

def likeStat(postID, userID):
	cmd = 'select * from  likes where postID = %s and userID = %s'
	mycursor.execute(cmd ,(postID,userID))
	mycursor.fetchall()
	if(mycursor.rowcount == 0):
		return False

	return True	

def get_fakes():
    cmd = 'select U.username , U.id from user as U where ((TO_DAYS( NOW()) - TO_DAYS(U.dtime) + 1) * 0.1 > (select count( TO_DAYS(P.dtime)) from post as P where P.posterID = U.id)) and (select count(L.postID) from likes as L where L.userID = U.id)*0.5 < (select count(LL.postID) from post as RO, likes as LL where LL.postID = RO.id and LL.userID = U.id group by RO.posterID order by count(LL.postID) desc limit 1) '    
    mycursor.execute(cmd)
    l = []
    for x in mycursor:
    	l.append((x[0] , x[1]))
    return l

def get_faker(fakeId):
    cmd = 'select username from user where id = (select RO.posterID from post as RO, likes as LL where LL.postID = RO.id and LL.userID = %s group by RO.posterID order by count(LL.postID) desc limit 1)'
    mycursor.execute(cmd , (fakeId,))
    l = []
    for x in mycursor:
    	l.append(x[0])
    return l

def numLike(postId):
    cmd = 'select count(userID) from likes where postID = %s'
    mycursor.execute(cmd ,(postId,))
    l = []
    for x in mycursor:
        l.append(x[0])
    return l[0]

def block(blockerID, blockedID):
	cmd = 'select * from block where blockerID = %s and blockedID = %s'
	mycursor.execute(cmd ,(blockerID,blockedID))
	mycursor.fetchall()
	if(mycursor.rowcount != 0):
		return False
	try:
		newcmd = 'insert into block(blockerID, blockedID) values (%s , %s )'
		mycursor.execute(newcmd , (blockerID , blockedID))
		#deleting follows
		cmd = 'select * from follow where followerID = %s and followedID = %s'
		mycursor.execute(cmd ,(blockerID,blockedID))
		mycursor.fetchall()
		if(mycursor.rowcount != 0):
			cmd = 'delete from follow where followerID = %s and followedID = %s'
			mycursor.execute(cmd ,(blockerID,blockedID))
		
		cmd = 'select * from follow where followerID = %s and followedID = %s'
		mycursor.execute(cmd ,(blockedID,blockerID))
		mycursor.fetchall()
		if(mycursor.rowcount != 0):
			cmd = 'delete from follow where followerID = %s and followedID = %s'
			mycursor.execute(cmd ,(blockedID,blockerID))
		
		mydb.commit()
		return True
	except:
		return False

def get_suggest_given(userId , givenId):
    cmd = 'select U.username , U.id from user as U , follow as F where(( U.id = F.followerID and F.followedID = %s ) or (U.id = F.followedID and F.followerID = %s)) and U.id not in(select Y.followedID from follow as Y where Y.followerID = %s) and U.id <> %s'
    mycursor.execute(cmd , (givenId,givenId , userId,userId))
    l = []
    for x in mycursor:
    	l.append( (x[0] , x[1]))
    return l

def unblock(blockerID, blockedID):
	cmd = 'select * from block where blockerID = %s and blockedID = %s'
	mycursor.execute(cmd ,(blockerID,blockedID))
	mycursor.fetchall()
	if(mycursor.rowcount == 0):
		return False
	try:
		newcmd = 'delete from block where blockerID = %s  and blockedID = %s '
		mycursor.execute(newcmd , (blockerID , blockedID))
		mydb.commit()
		return True
	except:
		return False

def followerCount(userId):
    cmd = 'select count(followerID) from follow where followedID = %s'
    mycursor.execute(cmd ,(userId,))
    l = []
    for x in mycursor:
        l.append(x[0])
    return l[0]

def followingCount(userId):
    cmd = 'select count(followedID) from follow where followerID = %s'
    mycursor.execute(cmd ,(userId,))
    l = []
    for x in mycursor:
        l.append(x[0])
    return l[0]

def getbio(userId):
    cmd = 'select bio from user where id = %s'
    mycursor.execute(cmd ,(userId,))
    l = []
    for x in mycursor:
        l.append(x[0])
    return l[0]

def getphoto(userId):
    cmd = 'select photoPath from user where id = %s'
    mycursor.execute(cmd ,(userId,))
    l = []
    for x in mycursor:
        l.append(x[0])
    return l[0]

def blockStat(blockerID, blockedID):
	cmd = 'select * from block where blockerID = %s and blockedID = %s'
	mycursor.execute(cmd ,(blockerID,blockedID))
	mycursor.fetchall()
	if(mycursor.rowcount == 0):
		return False
	return True

def follow(followerID, followedID):
    if blockStat(followedID , followerID):
        return False
    if blockStat(followerID , followedID):
        return False
    
    cmd = 'select * from follow where followerID = %s and followedID = %s'
    mycursor.execute(cmd ,(followerID,followedID))
    mycursor.fetchall()
    if(mycursor.rowcount != 0):
    	return False
    try:
    	newcmd = 'insert into follow(followerID, followedID) values (%s , %s )'
    	mycursor.execute(newcmd , (followerID , followedID))
    	mydb.commit()
    	return True
    except:
    	return False
	
def unfollow(followerID, followedID):
	cmd = 'select * from follow where followerID = %s and followedID = %s'
	mycursor.execute(cmd ,(followerID,followedID))
	mycursor.fetchall()
	if(mycursor.rowcount == 0):
		return False
	try:
		newcmd = 'delete from follow where followerID = %s  and followedID =  %s '
		mycursor.execute(newcmd , (followerID , followedID))
		mydb.commit()
		return True
	except:
		return False

def followStat(followerID, followedID):
	cmd = 'select * from follow where followerID = %s and followedID = %s'
	mycursor.execute(cmd ,(followerID,followedID))
	mycursor.fetchall()
	if(mycursor.rowcount == 0):
		return False
	return True

def get_suggest(userId):
    cmd = 'select U.username , U.id from user as U , follow as F where ( U.id = F.followerID and F.followedID = %s )  and U.id not in(select Y.followedID from follow as Y where Y.followerID = %s) and U.id <> %s'
    mycursor.execute(cmd , (userId , userId,userId))
    l = []
    for x in mycursor:
    	l.append( (x[0] , x[1]))
    return l

def search_hashtag(userId , hashtag):
    cmd = "(select P.text , P.id from post as P , follow  as F , hashtag as H where F.followerID = %s and F.followedID = P.posterID and H.text = %s and H.tweet_id = P.id)\
    union(select P.text , P.id from post as P  , hashtag as H where P.id in (select K.tweet_id from hashtag as K group by K.tweet_id having count(K.id)=2) and H.tweet_id = P.id and H.text = %s order by P.dtime desc)\
    union( select P.text, temp.b  from (select K.tweet_id as b  , count(K.id) as cid from hashtag as K where K.tweet_id in(select RO.tweet_id from hashtag as RO where RO.text = %s)group by K.tweet_id having count(K.id)>2) as temp , post as P where P.id = temp.b order by  temp.cid  asc   )  "
    mycursor.execute(cmd , (userId, hashtag, hashtag,hashtag ))
    l = []
    for x in mycursor:
    	l.append( (x[0] , x[1]))
    return l

def search_user( name):
    cmd = "select username , id from user where username like %s "
    mycursor.execute(cmd , ('%'+name+'%',))
    l = []
    for x in mycursor:
    	l.append( (x[0] , x[1]))
    return l

def get_hottest(userId):
    cmd = 'select ER.ptx , ER.ptid from (select P.text as ptx , P.id  as ptid , K.cid*0.3 + RO.cid*0.7+MO.cid*0.1 as o from post as P , (select L.postID as pid ,count(L.userID) as cid from likes as L group by L.postID)as K , (select W.tweet_id as pid ,count(W.id) as cid from comment as W group by W.tweet_id)as RO , (select C.tweet_id as pid ,count(LL.userID) as cid from likes as LL , comment as C where C.id = LL.postID  group by C.tweet_id)as MO where MO.pid = RO.pid and MO.pid = K.pid and MO.pid = P.id limit 100) as ER order by ER.o'
    mycursor.execute(cmd )
    l = []
    for x in mycursor:
    	l.append( (x[0] , x[1]))
    return l

def get_all_daily_actives():
	cmd = 'select U.username , U.id from user as U where (TO_DAYS( NOW()) - TO_DAYS(U.dtime) + 1) = (select count(distinct TO_DAYS(P.dtime)) from post as P where P.posterID = U.id) '
	print('meh')
	mycursor.execute(cmd)
	l = []
	for x in mycursor:
  		l.append((x[0] , x[1]))
	return l

def list_of_follow_backers():
	cmd = 'select U.username , U.id from user as U, follow as F where U.id = F.followedID and F.followerID in (select M.followedID from follow as M where M.followerID = U.id)'
	mycursor.execute(cmd)
	l = []
	for x in mycursor:
  		l.append( (x[0] , x[1]))
	return l

def get_type(userId):
    cmd = "select accountType from user where id = %s "
    mycursor.execute(cmd , (userId,))
    l = []
    for x in mycursor:
    	l.append( x[0] )
    return l[0]


def find_those_with_more_than_tree():
    cmd = "select U.username , U.id from user as U ,(select Q.i as o from (select P.posterID as i , P.id as pid  from post as P , comment as C where P.id = C.tweet_id group by C.tweet_id having count(C.tweet_id)>=10) as Q group by Q.i having count(Q.pid)>3)as W where W.o = U.id"
    mycursor.execute(cmd)
    l = []
    for x in mycursor:
    	l.append( (x[0] , x[1]))
    return l

class StudentListButton(ListItemButton):
    pass

class LoginScreen(GridLayout):

    def __init__(self, **kwargs):
        super(LoginScreen, self).__init__(**kwargs)
        self.cols = 4
        self.username = ''
        self.userId = 0
        self.opened_userId = 0
        self.userType = -1
        self.postId = 0
        self.passwordbox = TextInput(password=True, multiline=False)
        self.usernamebox = TextInput(multiline=False)
        self.biobox = TextInput(multiline=False)
        self.postText = TextInput()
        self.hashtags = TextInput()
        self.back = Button(text='back', font_size=14)
        self.back.bind(on_press = self.callback_back)
        self.email = TextInput(multiline=False)
        self.pic_address = TextInput(multiline=False)
        self.add_widget(self.back)
        self.lt_ans = TextInput(multiline=False)
        # self.back.bind
        self.back_names = []
        self.cur_name = 'main'
        self.login = Button(text='login', font_size=14)
        self.login.bind(on_press = self.callback_login)
        self.login_check = Button(text = 'login' , font_size = 14)
        self.login_check.bind(on_press = self.callback_login_check)
        self.stat_shower = Label()
        self.sign_check = Button(text = 'sing_up' , font_size = 14)
        self.sign_check.bind(on_press = self.callback_sign_check)

        self.like = Button(text = 'like' , font_size = 14)
        self.like.bind(on_press = self.callback_like)

        self.hottest = Button(text = 'hot post' , font_size = 14)
        self.hottest.bind(on_press = self.callback_hottest)

        self.fakes = Button(text = 'fakes' , font_size = 14)
        self.fakes.bind(on_press = self.callback_fakes)

        self.faker = Button(text = 'faker' , font_size = 14)
        self.faker.bind(on_press = self.callback_faker)

        self.dislike = Button(text = 'dislike' , font_size = 14)
        self.dislike.bind(on_press = self.callback_dislike)

        # self.login_stat_shower = Label()
        self.forget_check = Button(text = 'change_pass' , font_size = 14)
        self.forget_check.bind(on_press = self.callback_forget_check)

        self.follow_post = Button(text = 'follower_post' , font_size = 14)
        self.follow_post.bind(on_press = self.callback_follow_post)

        self.three = Button(text = 'three' , font_size = 14)
        self.three.bind(on_press = self.callback_three)


        self.post = Button(text = 'post' , font_size = 14)
        self.post.bind(on_press = self.callback_post)

        self.openComment = Button(text = 'open_comment_or_rep' , font_size = 14)
        self.openComment.bind(on_press = self.callback_openComment)

        self.suggest = Button(text = 'suggest' , font_size = 14)
        self.suggest.bind(on_press = self.callback_suggest)
        

        self.follow = Button(text = 'follow' , font_size = 14)
        self.follow.bind(on_press = self.callback_follow)

        self.seach_user = Button(text = 'search_user' , font_size = 14)
        self.seach_user.bind(on_press = self.callback_seach_user)

        self.seach_hashtag = Button(text = 'seach_hashtag' , font_size = 14)
        self.seach_hashtag.bind(on_press = self.callback_seach_hashtag)


        self.block = Button(text = 'block' , font_size = 14)
        self.block.bind(on_press = self.callback_block)
        
        self.unfollow = Button(text = 'unfollow' , font_size = 14)
        self.unfollow.bind(on_press = self.callback_unfollow)

        self.unblock = Button(text = 'unblock' , font_size = 14)
        self.unblock.bind(on_press = self.callback_unblock)

        self.comment = Button(text = 'comment' , font_size = 14)
        self.comment.bind(on_press = self.callback_comment)


        self.open_user = Button(text = 'open_user' , font_size = 14)
        self.open_user.bind(on_press = self.callback_open_user)

        self.openPost = Button(text = 'open' , font_size = 14)
        self.openPost.bind(on_press = self.callback_openPost)

        self.post_check = Button(text = 'post' , font_size = 14)
        self.post_check.bind(on_press = self.callback_post_check)

        self.open_in_new = Button(text = 'open user' , font_size = 14)
        self.open_in_new.bind(on_press = self.callback_post_open_in_new)

        self.daily = Button(text = 'daily active' , font_size = 14)
        self.daily.bind(on_press = self.callback_daily)

        self.follow_backers = Button(text = 'follow backs' , font_size = 14)
        self.follow_backers.bind(on_press = self.callback_follow_backers)

        self.sign_up = Button(text='sign up', font_size=14)
        self.sign_up.bind(on_press = self.callback_sign)
        self.forget_pass = Button(text='forget pass', font_size=14)
        self.forget_pass.bind(on_press = self.callback_forget)

        # # self.add_widget(Label(text='User Name'))
        # # self.username = TextInput(multiline=False)
        # # self.add_widget(self.username)
        # # self.add_widget(Label(text='password'))
        # # self.password = TextInput(password=True, multiline=False)
        # # self.add_widget(self.password)
        
        self.add_widget(self.login)
        self.add_widget(self.sign_up)
        # self.add_widget(self.forget_pass)
        simple_list_adapter = ListAdapter(data=[],cls=StudentListButton)
        self.lt = ListView(adapter=simple_list_adapter)
        not_simple_list_adapter = ListAdapter(data=[],cls=StudentListButton)
        self.newlt = ListView(adapter=not_simple_list_adapter)
        # self.lt.bind(on_press=self.cb)
        # self.lt.adaptor = ListAdapter(data=["Doug Smith"])
        # self.add_widget(self.lt)
        
        # self.lt.data.extend(['mynamr'])
        # self.lt._trigger_reset_populate()
        # self.add_widget(Button(text='Hello world', font_size=14))
        # self.btn1 = Button(text="OK")
        # self.btn1.bind(on_press=self.buttonClicked)
        # self.add_widget(self.btn1)
        # self.lbl1 = Label(text="test")
        # self.add_widget(self.lbl1)
        # self.txt1 = TextInput(text='', multiline=False)
        # self.add_widget(self.txt1)
        # return layout

    def clc(self):
        self.remove_widget(self.login)
        self.remove_widget(self.sign_check)
        self.remove_widget(self.forget_pass)
        self.remove_widget(self.sign_up)
        self.remove_widget(self.lt)
        for _ in range(len(self.lt.adapter.data)):
            del self.lt.adapter.data[0]
        self.remove_widget(self.newlt)
        for _ in range(len(self.newlt.adapter.data)):
            del self.newlt.adapter.data[0]
        self.remove_widget(self.login_check)
        self.remove_widget(self.postText)
        self.remove_widget(self.hashtags)
        # self.remove_widget(self.forget_pass)
        self.remove_widget(self.usernamebox)
        self.remove_widget(self.passwordbox)
        self.remove_widget(self.stat_shower)
        self.remove_widget(self.biobox)
        self.remove_widget(self.lt_ans)
        self.remove_widget(self.email)
        self.remove_widget(self.pic_address)
        self.remove_widget(self.forget_check)
        self.remove_widget(self.post)
        self.remove_widget(self.follow_post)
        self.remove_widget(self.open_user)
        self.remove_widget(self.post_check)
        self.remove_widget(self.openPost)
        self.remove_widget(self.comment)
        self.remove_widget(self.openComment)
        self.remove_widget(self.like)
        self.remove_widget(self.dislike)
        self.remove_widget(self.follow)
        self.remove_widget(self.unblock)
        self.remove_widget(self.unfollow)
        self.remove_widget(self.block)
        self.remove_widget(self.open_in_new)
        self.remove_widget(self.suggest)
        self.remove_widget(self.seach_user)
        self.remove_widget(self.seach_hashtag)
        self.remove_widget(self.hottest)
        self.remove_widget(self.daily)
        self.remove_widget(self.follow_backers)
        self.remove_widget(self.three)
        self.remove_widget(self.faker)
        self.remove_widget(self.fakes)
    
    def callback_back(self, instance):
        if(len(self.back_names) > 0):
            self.clc()
            self.cur_name = self.back_names[-1]
            del self.back_names[-1]
            if(self.cur_name == 'main'):
                self.show_main()
            if(self.cur_name == 'login'):
                self.show_login()
            if(self.cur_name == 'menu'):
                self.show_menu()
            print('here')
            
    def callback_sign(self,instance):
        self.back_names.append(self.cur_name)
        self.clc()
        self.cur_name = 'sign_up'
        self.show_signup()

    def callback_login(self,instance):
        self.back_names.append(self.cur_name)
        self.clc()
        self.cur_name = 'login'
        self.show_login()

    def callback_forget(self, instance):
        if(self.usernamebox.text != '' and hasUser(self.usernamebox.text)):
            self.username = self.usernamebox.text
            self.back_names.append(self.cur_name)
            self.clc()
            self.cur_name = 'forget'
            self.show_forget()

    def callback_post(self , instance):
        self.clc()
        self.back_names.append(self.cur_name)
        self.cur_name = 'post'
        self.show_post()


    def callback_follow_post(self, instance):
        self.back_names.append(self.cur_name)
        self.clc()
        self.cur_name = 'follow_post'
        posts = get_last_hdposts(self.userId)
        self.postShower(posts)
        
    def callback_openPost(self , instance):
        if(self.lt.adapter.selection):
            
            self.cur_name = 'openPost'
            self.postId = self.lt.adapter.selection[0].text.split(',')[-1]
            self.stat_shower.text = self.lt.adapter.selection[0].text
            self.clc()
            self.show_post_inside()

    def callback_comment(self , instance):
        res = comment(self.userId , self.postId , self.biobox.text)
        if res == False:
            self.biobox.text = 'you have passed depth'

    def callback_dislike(self , instance):
        unlike(self.postId , self.userId)
    
    def callback_like(self , instance):
        if(blockStat(self.userId , get_user_id(self.postId)) == False  and  blockStat( get_user_id(self.postId),self.userId) == False):
            like(self.postId , self.userId)

    def callback_follow(self, instance):
        follow(self.userId , self.opened_userId)

    def callback_unfollow(self, instance):
        unfollow(self.userId , self.opened_userId)

    def callback_block(self, instance):
        block(self.userId , self.opened_userId)    

    def callback_unblock(self, instance):
        unblock(self.userId , self.opened_userId)

    def callback_openComment(self , instance):
        if(self.lt.adapter.selection):
            self.cur_name = 'opencomment'
            self.postId = self.lt.adapter.selection[0].text.split(',')[-1]
            self.stat_shower.text = self.lt.adapter.selection[0].text
            self.clc()
            self.show_comment_inside()

    def callback_open_user(self, instance):
        print(self.userId)
        self.opened_userId = get_user_id(self.postId)
        self.cur_name = 'user'
        self.clc()
        self.show_user()

    def callback_suggest(self, isinstance):
        self.back_names.append(self.cur_name)
        self.clc()
        self.cur_name = 'suggest'
        r = get_suggest(self.userId)
        self.show_user_menu(r)

    def callback_post_open_in_new(self, instance):
        if(self.newlt.adapter.selection):
            self.opened_userId = self.newlt.adapter.selection[0].text.split(',')[-1]
            self.cur_name = 'user'
            self.clc()
            self.show_user()
        
    def show_user(self):
        if(blockStat(self.userId , self.opened_userId) == False and blockStat(self.opened_userId , self.userId) == False):
            self.add_widget(self.lt)
            ps = get_user_posts(self.opened_userId)
            for i in ps:
                self.lt.adapter.data.extend([str(i[0])+',' + str(i[1])])
            self.lt._trigger_reset_populate()
            self.add_widget(self.openPost)
        if(followStat(self.userId , self.opened_userId) == False):
            self.add_widget(self.follow)
        else:
            self.add_widget(self.unfollow)
        if(blockStat(self.userId , self.opened_userId) == False):
            self.add_widget(self.block)
        else:
            self.add_widget(self.unblock)
        self.stat_shower.text = 'followers:\n' + str( followerCount(self.opened_userId) ) + '\n' + 'following:\n' + str( followingCount(self.opened_userId) ) + '\n' + 'bio:\n' + str( getbio(self.opened_userId) )+ '\n' + 'photo:\n' + str( getphoto(self.opened_userId))
        sug = get_suggest_given(self.userId , self.opened_userId)
        self.add_widget(self.stat_shower)
        for i in sug:
            self.newlt.adapter.data.extend([str(i[0])+',' + str(i[1])])
        self.newlt._trigger_reset_populate()
        self.add_widget(self.newlt)
        self.add_widget(self.open_in_new)

    def show_comment_inside(self):
        self.add_widget(self.stat_shower)
        comments = get_reps(self.postId)
        for i in comments:
            self.lt.adapter.data.extend([str(i[0])+',' + str(i[1])])
        self.lt._trigger_reset_populate()
        self.add_widget(self.lt)
        self.add_widget(self.open_user)
        self.biobox.text = 'enter comment'
        self.add_widget(self.biobox)
        self.add_widget(self.comment)
        self.add_widget(self.openComment)
        if(likeStat(self.postId , self.userId)):
            self.add_widget(self.dislike)
        else:
            self.add_widget(self.like)

    def show_post_inside(self):
        lks = numLike(self.postId)
        self.stat_shower.text = self.stat_shower.text + '\n' + str(lks)
        self.add_widget(self.stat_shower)
        comments = get_comments(self.postId)
        for i in comments:
            self.lt.adapter.data.extend([str(i[0])+',' + str(i[1])])
        self.lt._trigger_reset_populate()
        self.add_widget(self.lt)
        self.add_widget(self.open_user)
        self.biobox.text = 'enter comment'
        self.add_widget(self.biobox)
        self.add_widget(self.comment)
        self.add_widget(self.openComment)
        if(likeStat(self.postId , self.userId)):
            self.add_widget(self.dislike)
        else:
            self.add_widget(self.like)


    def postShower(self , posts):
        for i in posts:
            self.lt.adapter.data.extend([str(i[0])+',' + str(i[1])])
        self.lt._trigger_reset_populate()
        self.add_widget(self.lt)
        self.add_widget(self.openPost)

    def show_user_menu(self , users):
        for i in users:
            self.newlt.adapter.data.extend([str(i[0])+',' + str(i[1])])
        self.newlt._trigger_reset_populate()
        self.add_widget(self.newlt)
        self.add_widget(self.open_in_new)

    def show_menu(self):
        self.add_widget(self.follow_post)
        self.add_widget(self.post)
        self.add_widget(self.suggest)
        self.biobox.text = 'search'
        self.add_widget(self.biobox)
        self.add_widget(self.seach_user)
        self.add_widget(self.seach_hashtag)
        self.add_widget(self.hottest)
        if(get_type(self.userId) > 1):
            self.add_widget(self.daily)
            self.add_widget(self.follow_backers)
        if(get_type(self.userId) > 2):
            self.add_widget(self.three)
            self.add_widget(self.fakes)

    def show_forget(self):
        difq = get_dif_q(self.username)
        self.stat_shower.text = 'enter answer\n and new pass\n'+str(difq)
        self.add_widget(self.stat_shower)
        self.biobox.text = 'answer'
        self.add_widget(self.biobox)
        self.add_widget(self.passwordbox)
        self.add_widget(self.forget_check)
        # self.add_widget(self. )
    
    def show_fake_menu(self , users):
        for i in users:
            self.newlt.adapter.data.extend([str(i[0])+',' + str(i[1])])
        self.newlt._trigger_reset_populate()
        self.stat_shower.text = ''
        self.add_widget(self.stat_shower)
        self.add_widget(self.newlt)
        self.add_widget(self.open_in_new)
        self.add_widget(self.faker)

    def callback_faker(self , instance):
        if(self.newlt.adapter.selection):
            # self.cur_name = 'opencomment'
            clk = self.newlt.adapter.selection[0].text.split(',')[-1]
            self.stat_shower.text = str(get_faker(clk))
            # self.clc()
            # self.show_comment_inside()

    def callback_fakes(self, instance):
        self.back_names.append(self.cur_name)
        self.clc()
        self.cur_name = 'search'
        r = get_fakes()
        print(r)
        self.show_fake_menu(r) 



    def show_login(self):
        self.stat_shower.text = 'plz enter user pass'
        self.add_widget(self.stat_shower)
        self.add_widget(self.usernamebox)
        self.add_widget(self.passwordbox)
        self.add_widget(self.login_check)
        self.add_widget(self.forget_pass)

    def show_main(self):
        self.add_widget(self.login)
        self.add_widget(self.sign_up)
        # self.add_widget(self.forget_pass)
    
    def show_signup(self):
        self.stat_shower.text = 'please enter\n username\n password\n email\n pic_address\n bio\n difQ\n ansto difq\n'
        self.pic_address.text = '~/1.png'
        self.biobox.text = 'empty bio'
        self.add_widget(self.stat_shower)
        self.add_widget(self.sign_check)
        self.add_widget(self.usernamebox)
        self.add_widget(self.passwordbox)
        self.add_widget(self.email)
        self.add_widget(self.pic_address)
        self.add_widget(self.biobox)
        self.add_widget(self.lt)
        rt = get_dif_qs()
        for i in rt:
            self.lt.adapter.data.extend([str(i[0])+',' + str(i[1])])
        self.lt._trigger_reset_populate()
        self.add_widget(self.lt_ans)

    def show_post(self):
        self.stat_shower.text = 'plz enter postText\nhastags with comma'
        self.add_widget(self.stat_shower)
        self.add_widget(self.postText)
        self.add_widget(self.hashtags)
        self.add_widget(self.post_check)

    def callback_daily(self, instance):
        self.back_names.append(self.cur_name)
        self.clc()
        self.cur_name = 'search'
        r = get_all_daily_actives()
        print(r)
        self.show_user_menu(r)

    def callback_follow_backers(self, instance):
        self.back_names.append(self.cur_name)
        self.clc()
        self.cur_name = 'search'
        r = list_of_follow_backers()
        self.show_user_menu(r)

    def callback_three(self, instance):
        self.back_names.append(self.cur_name)
        self.clc()
        self.cur_name = 'search'
        r = find_those_with_more_than_tree()
        self.show_user_menu(r)

    def callback_seach_user(self, instance):
        self.back_names.append(self.cur_name)
        self.clc()
        self.cur_name = 'search'
        r = search_user(self.biobox.text)
        self.show_user_menu(r)

    def callback_seach_hashtag(self, instance):
        self.back_names.append(self.cur_name)
        self.clc()
        self.cur_name = 'search'
        r = search_hashtag(self.userId , self.biobox.text)
        self.postShower(r)

    def callback_hottest(self , instance):
        self.back_names.append(self.cur_name)
        self.clc()
        self.cur_name = 'search'
        r = get_hottest(self.userId)
        self.postShower(r)

    def callback_post_check(self, instance):
        hastags = self.hashtags.text.split(',')
        res = tweet(self.userId , self.postText.text , hastags)
        if (res == False):
            self.stat_shower.text = 'plz check input\n posttext\n hastags with comma'
        else:
            self.stat_shower.text = 'done!'
    
    def callback_login_check(self , instance):
        username = self.usernamebox.text
        password = self.passwordbox.text
        res = login(username,password)
        print(res)
        if(res == -1):
            self.stat_shower.text = 'wrong username or password'
        else:
            self.username = username
            self.userType = res[0]
            print(res)
            self.userId = res[1]
            # print(self)
            self.clc()
            self.back_names = []
            self.cur_name = 'menu'
            self.show_menu()
    
    def callback_sign_check(self, instance):
        # ress = False
        if self.lt.adapter.selection and self.lt_ans.text != '' and self.usernamebox.text != '' and self.passwordbox.text != ''  and self.email.text != '' :
            qid = self.lt.adapter.selection[0].text.split(',')[-1]
            if(self.pic_address.text == ''):
                res = add_new_user(self.usernamebox.text , self.email.text , self.passwordbox.text,qid,self.lt_ans.text,1,bio = self.biobox.text)
            else:
                res = add_new_user(self.usernamebox.text , self.email.text , self.passwordbox.text,qid,self.lt_ans.text,1,bio = self.biobox.text,photopath=self.pic_address.text)
            if(res == False):
                self.stat_shower.text = 'wrong user,pass\n,email\nplease enter\n username\n password\n email\n pic_address\n bio\n difQ\n ansto difq\n'
            else:
                self.stat_shower.text = 'done! plz log in'
        else:
            self.stat_shower.text = 'please enter\n req fields\nplease enter\n username\n password\n email\n pic_address\n bio\n difQ\n ansto difq\n'   

    def callback_forget_check(self, instance):
        res = change_pass(self.username , self.passwordbox.text , self.biobox.text)

        if(res == True):
            self.stat_shower.text = 'pass changed'
        else:
            difq = get_dif_q(self.username)
            self.stat_shower.text = 'try again\n' + difq
    

    def buttonClicked(self,btn):
        self.lbl1.text = "You wrote " + self.txt1.text
        self.remove_widget(self.txt1)
    

class MyApp(App):

    def build(self):
        return LoginScreen()


class TestApp(App):

    def build(self):
        return LoginScreen()

# button click function

if __name__ == '__main__':
    TestApp().run()

# if __name__ == '__main__':
#     MyApp().run()