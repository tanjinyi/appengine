#!/usr/bin/env python

import webapp2  # web application framework
import jinja2 # template engine
import os   # access file system
import datetime # format date time
import urllib # get from url
import logging # logging debug because >debug
from google.appengine.api import users  # Google account authentication
from google.appengine.ext import db   # datastore
from google.appengine.api import mail # send email

# initialize template
jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class report(db.Expando):
  user = db.StringProperty() # username
  #userclass = db.StringProperty(multiline=False)
  record = db.StringProperty(multiline=True)
  date = db.DateTimeProperty(auto_now_add=True)
  status = db.StringProperty(multiline=False)
  errortype = db.StringProperty(choices=set(['AV', 'IT', 'General']))
  reportid = db.IntegerProperty()
  remark = db.StringProperty()

def next_record_id():
  posts = db.GqlQuery('SELECT * FROM report ORDER BY reportid DESC')
  if posts.count() == 0:
    return 0
  else:
    return posts[0].reportid + 1
          

class usergroup(db.Model):
  user = db.StringProperty(multiline=False)
  admin = db.BooleanProperty()

def report_key(report_name=None):
  return db.Key.from_path('report', report_name or 'default_report')

class MainPage(webapp2.RequestHandler):
  def get(self):
    user = users.get_current_user()
    nickname = user.email() # change for deployment
    errhandle = "all"
    report_name = self.request.get('report_name')
    reports_query = report.all().ancestor(
      report_key(report_name)).order('-date')
    reports = reports_query.fetch(100)
    superusers = ["help@dhs.sg", "chia.leekwang@dhs.sg", "choo.yewseng@dhs.sg", "tan.jinyi.ambrose@dhs.sg"]
    if user:
      url = users.create_logout_url(self.request.uri)
      url_linktext = "Sign out"
    else:
      url = users.create_login_url(self.request.uri)
      url_linktext = "Sign in"
    if nickname == "help@dhs.sg":
      errhandle = "IT"
    elif nickname == "chia.leekwang@dhs.sg":
      errhandle = "AV"
    elif nickname == "choo.yewseng@dhs.sg":
      errhandle = "general"
    template_values = {
      'errhandle' : errhandle,
      'reports' : reports,
      'user' : user,
      'url': url,
      'url_linktext': url_linktext,
    }
    if nickname in superusers:
      template = jinja_environment.get_template('indexadmin.html')
    else:
      template = jinja_environment.get_template('index.html')
    self.response.out.write(template.render(template_values))

class Archives(webapp2.RequestHandler):
  def post(self):
    report_name = self.request.get('report_name')
    records = report(parent=report_key(report_name))
    records.reportid = next_record_id()                      
    records.user = users.get_current_user().nickname()
    records.record = self.request.get('content') # grabs content for id content
    records.errortype = self.request.get('option')
    records.status = "Not seen"
    records.put()
    self.redirect('/?' + urllib.urlencode({'report_name': report_name}))

class EditStatus(webapp2.RequestHandler):
  def post(self):
    report_satatus = self.request.get('report_status') # a-ok
    updated_status = self.request.get('update') # a-ok
    report_remark = self.request.get('remark') 
    update_id = int(self.request.get('id')) # wow, all because of this? fegs
    query = db.GqlQuery("SELECT * FROM report WHERE reportid=:1", update_id)
    result = query.fetch(1)
    if result:
      record = result[0]
      record.status = updated_status
      if report_remark:
        record.remark = report_remark
      record.put()
    self.redirect('/')

class Delete(webapp2.RequestHandler):
  def post(self):
    delete_id = int(self.request.get('id'))
    delete_query = self.request.get('delete')
    if (delete_query == "yes"):
      query = db.GqlQuery("SELECT * FROM report WHERE reportid=:1", delete_id)
      result = query.fetch(1)
      for item in result:
        db.delete(item)
    self.redirect('/')
    
app = webapp2.WSGIApplication([('/', MainPage), ('/submit', Archives), ('/update', EditStatus), ('/delete', Delete)],
debug=True)
