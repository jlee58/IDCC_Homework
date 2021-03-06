# -*- coding: utf-8 -*-
import requests
import urllib2
import re
from bs4 import BeautifulSoup
import MySQLdb
import socket
import datetime

requests.packages.urllib3.disable_warnings()

# drama-ticket url
url_ticket = "https://www.ptt.cc/bbs/Drama-Ticket/index.html"
page_id = 0
record_post_id = 0
singers = []

def connectDB():
	try:
		conn = MySQLdb.connect(host="localhost", user="root", passwd="123456qqq", db="data")
		conn.set_character_set('utf8')
		return conn
	except socket.error as serror:
		if conn is not None:
			conn.close()

def closeDB(conn):
	conn.close()

def loadSinger(conn):
	global singers
	c = conn.cursor()
	sql = "SELECT * FROM singer WHERE active = 1"
	
	try:
		c.execute(sql)
		singers = c.fetchall()
		#get the singers where active = 1
	except MySQLdb.Error,e:
		print e
	
def insertDB(conn,postid,title,author,time,process,singer,singerid,price,num,raw,url):

	c = conn.cursor()
	sql = "INSERT INTO ptt(postid,title,author,time,process,singer,singerid,price,num,raw,url) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
	#print sql
	try:
		c.execute(sql,(postid,title,author,time,process,singer,singerid,price,num,raw,url) )
		conn.commit()
	except MySQLdb.Error,e:
		print "Mysql Error %d: %s" % (e.args[0], e.args[1])


def read():
	global record_post_id
	file = open("log.txt", 'r')
	record_post_id = int(file.read())

def save():
	global record_post_id
	file = open("log.txt", 'w')
	file.write(str(record_post_id))
	file.close()

def getFirstPage():
	global page_id
	res = requests.get(url_ticket, verify=False)
	first_page = re.search(r'href="/bbs/Drama-Ticket/index(\d+).html">&lsaquo;', res.text).group(1)
	page_id = int(first_page)+1

def test_getManyPage(conn,num):
	global page_id
	page_id = page_id-num
	i = num
	print 'auto'
	while i>0:
		getPage(conn)
		i -=1
		page_id = page_id + 1
		
def getSinger(title,singers,sdata):

	success = 0
	for singer in singers:
		s = re.search(singer[3], title, re.IGNORECASE)
		#compare singer name with raw title
		if s is not None:
			#find singer name in title
			#title = s.group()
			success = 1
			sdata[0] = singer[1]
			sdata[1] = singer[3]
			break
		else:
			pass
	return success

def getPage(conn):
	global page_id
	global record_post_id
	global singers
	post_id = record_post_id
	count = 1
	res = requests.get("https://www.ptt.cc/bbs/Drama-Ticket/index"+str(page_id)+".html", verify=False)
	soup = BeautifulSoup(res.text,'html.parser')
	ss=""
	for entry in soup.select('.r-ent'):
		try:
			title = entry.select('.title')[0].text.encode('utf-8').strip('\n')
			if not re.search(r'本文已被刪除', title) and not re.search(r'公告', title) and not re.search(r'Re:', title) and not re.search(r'展', title) and re.search(r'售', title):
				url = "https://www.ptt.cc" + entry.select('.title')[0].a.get('href').encode('utf-8')
				post_id = (page_id-1)*20 + count
				if record_post_id < post_id:
				
					#get content
					res_post = requests.get(url, verify=False)
					soup_post = BeautifulSoup(res_post.text,'html.parser')
					metanum = soup_post.select('.article-meta-value')
					if(len(metanum)<3):
						continue
					content_post = soup_post.select('#main-content')[0].text.encode('utf-8')
					raw = content_post[content_post.find('2016')+5:content_post.find('--')].rstrip()
					author_t = soup_post.select('.article-meta-value')[0].text.encode('utf-8')
					author = ''
					author = author_t[0:author_t.find(' (')]
					time_t = soup_post.select('.article-meta-value')[3].text.encode('utf-8')
					if time_t[len(time_t)-1] == 'y':
						continue
					try:
						time = datetime.datetime.strptime(time_t, "%a %b  %d %H:%M:%S %Y").strftime('%Y-%m-%d %H:%M:%S')
					except IOError,ValueError:
						pass
					#process data
					sdata = [0,'']
					process_flag = 0
					if (getSinger(title,singers,sdata)):
						process_flag = 1
					print sdata[0], sdata[1]
					
					#insert
					#insertDB(conn,postid,title,author,time,process,concert,price,num,raw)
					#insertDB(conn,post_id,title,author,time,process_flag,sdata[1],sdata[0],0,0,raw,url)
					#print post_id, title, author, time
					#print url, raw
					
		except IOError as e:
			pass
			#print "I/O error({0}): {1}".format(e.errno, e.strerror)
		count = count + 1
	record_post_id = post_id
 
conn = None
conn = connectDB()

read() 
loadSinger(conn)
getFirstPage()
#print page_id
getPage(conn)
#test_getManyPage(conn,100)
save()

closeDB(conn)

#print page_id
#print record_post_id