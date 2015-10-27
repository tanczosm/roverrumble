#!/usr/bin/env python
# This Python file uses the following encoding: utf-8
#import cgi
#import datetime
import wsgiref.handlers
import time
#try:
#    import json
#except:
#    import simplejson as json
import string
import marshal
import zlib
import pickle

#from google.appengine.ext import db
#from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api import memcache
#from operator import attrgetter
import structures
#from structures import global_dict
class RumbleSelect(webapp.RequestHandler):
    def get(self):
        #global global_dict
        global_dict = {}
        starttime = time.time()
        query = self.request.query_string
        query = query.replace("%20"," ")
        parts = query.split("&")
        requests = {}
        if parts[0] != "":
            for pair in parts:
                ab = pair.split('=')
                requests[ab[0]] = ab[1]
        
        timing = bool(requests.get("timing",False))
        regen = bool(requests.get("regen",False))
        
        
        extraArgs = ""
        
        
        if timing:
            extraArgs += "&amp;timing=1"
        outstr = global_dict.get("home",None)
        if outstr is None and not regen:
            outstr = memcache.get("home")
        if outstr is None or regen:
            
            #gameHref = "<a href=Rankings?game=" + game + extraArgs + ">" + game + "</a>"
            out = []
            
            out.append(structures.html_header % ("Home","LiteRumble - Home"))
            
            q = structures.Rumble.all()
            
            rumbles = [[],[],[]]
            categories = ["1v1","Melee","Teams"]
            
            for r in q.run():
                memr = memcache.get(r.Name)
                if memr is not None:
                    r = memr
                    
                if r.Melee:
                    rumbles[1].append(r)
                elif r.Teams:
                    rumbles[2].append(r)
                else:
                    rumbles[0].append(r)
            
            for cat,rumbs in zip(categories,rumbles):
                for r in rumbs:
                    try:
                        scoresdicts = pickle.loads(zlib.decompress(r.ParticipantsScores))
                        entries = len(scoresdicts)
#                   print entries
#                   try:
#                       print "fun!"
                    except:
                        try:
                            scores = marshal.loads(zlib.decompress(r.ParticipantsScores))
                            entries = len(scores)
                        except:
                            entries = len(r.Participants)
                    r.__dict__["entries"] = entries 
                rumbs.sort(key = lambda r: -r.__dict__["entries"])
                
                out.append(  "<table class=\"rumble\">\n<tr>")
                
                out.append(  "\n<th colspan=\"2\">" + cat + "</th>\n<th>Participants</th>\n</tr>")
                
                for i,r in enumerate(rumbs):
                    game = r.Name
                    gameHref = "<a href=\"Rankings?game=" + game + extraArgs + "\" >" + game + "</a>"
                    topHref = "<a href=\"Rankings?game=" + game +"&amp;limit=50"+ extraArgs + "\" >top 50</a>"
                        
                    out.append( "\n<tr>\n<td>" + gameHref + "</td>\n<td>" + topHref + "</td>\n<td>")
                    out.append(str(r.__dict__["entries"]) + "</td>\n</tr>")
                    r.__dict__.pop("entries",1)
                    memcache.set(r.Name,r)
            
                out.append(  "</table>")
            
            out.append("<table><tr><td><b><a href=\"RumbleStats\">LiteRumble Statistics</a></b></td></tr>")
            out.append("<tr><td><b><a href=\"ScoreExplanation\">Score Explanation</a></b></td></tr></table>")
            
            out.append("<small><small>The LiteRumble costs ~$2/week in server time and database access.")
            out.append("\n<br>If you want help with these costs, please donate via Paypal. </small></small><br>")
            out.append(
                '''<form action="https://www.paypal.com/cgi-bin/webscr" method="post" target="_top">
                <input type="hidden" name="cmd" value="_s-xclick">
                <input type="hidden" name="hosted_button_id" value="QGM5KMPM5CTWU">
                <input type="image" src="https://www.paypalobjects.com/en_GB/i/btn/btn_donate_SM.gif" border="0" name="submit" alt="PayPal - The safer, easier way to pay online.">
                <img alt="" border="0" src="https://www.paypalobjects.com/en_US/i/scr/pixel.gif" width="1" height="1">
                </form>''')
            
            outstr = string.join(out,"")
            if not timing:
                memcache.set("home",outstr)
            
        elapsed = time.time() - starttime
        if timing:
            outstr += "<br>\n Page served in " + str(int(round(elapsed*1000))) + "ms."
        
        
        
        outstr += "</body></html>"

        self.response.out.write(outstr)


application = webapp.WSGIApplication([
    ('/RumbleSelect', RumbleSelect),
    ('/',RumbleSelect)
], debug=True)


def main():
    wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
    main()
