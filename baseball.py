#%%
import os
import copy
from lxml import html, etree
import requests
import math
import numpy as np
import urllib

# Getting Information from web pages
def DownLoadPage(url):
    response = urllib.request.urlopen(url)
    dat = str(response.read())
    return dat[4:-1]

def FindNextUrl( dat, team = 'Kansas City Athletics'):
    loc1 = dat.find('Next Game')
    loc2 = dat.find('Next Game',loc1+1)
    # one of these is correct
    loc3 = dat.find(team,loc1-400,loc1)
    if loc3==-1:
        loc1=loc2
        loc3 = dat.find(team,loc2-400)
    # move forward
    loc4 = dat.find('href',loc1-80)
    loc5a = dat.find('"',loc4)
    loc5b = dat.find('"',loc5a+1)
    #print(loc1,loc3,loc4,loc5a,loc5b)
    newurl = 'https://www.baseball-reference.com/'+dat[loc5a+2:loc5b]
    return newurl

def DownloadFiles(starturl, outdir, team='Washington Nationals', N=5):
    url = starturl
    for i in range(N):
        print(url)
        dat = DownLoadPage(url)
        n = url.rfind('/')
        nexturl = FindNextUrl(dat,team)
        fp = open(outdir + url[n:],'w')
        a = dat.split('\\'+'n') # newline is screwy in file
        a = '\n'.join(a)
        fp.write(a)
        url = nexturl
    return nexturl

# To get data directly from the webpage
# CUrrently NOT working
def SnarfWeb(urlname):
    webpage = requests.get(urlname)
    page = str(html.fromstring(webpage))
    print(len(page))
    page = page.replace('<!--\n','')
    page = page.replace('-->\n','')
    tree = html.fromstring(page)
    outs = tree.xpath('//td[@data-stat="outs"]/text()')
    onbase = tree.xpath('//td[@data-stat="runners_on_bases_pbp"]/text()')
    return outs, onbase

# #######################################3
# Collecting data from stored pages
def GetOutsBases(fname):
    with open(fname) as f:
        page = f.read()
    page = page.replace('<!--','')
    page = page.replace('-->','')
    tree = html.fromstring(page)
    outs = tree.xpath('//td[@data-stat="outs"]/text()')
    onbase = tree.xpath('//td[@data-stat="runners_on_bases_pbp"]/text()')
    # remove the top 5 plays
    outs = outs[5:]
    onbase = onbase[5:]
    return outs, onbase

def ToInnings(outs,onbase):
    innings = []
    N = len(outs)
    st = [outs[0] + onbase[0]]
    for i in range(1,N):
        if outs[i]=='0' and outs[i-1]!='0':
            st.append('3---')
            innings.append( st )
            st = ['0---']
        else:
            tostring = outs[i] + onbase[i]
            st.append(tostring)
    # last atbats
    st.append('3---')
    innings.append(st)
    return innings

def AddEvent(fromstring,tostring,dct):
    if fromstring not in dct:
        d = {}
        d[tostring] = 1
        dct[fromstring] = d
    else:
        if tostring not in dct[fromstring]:
            dct[fromstring][tostring] = 1
        else:
            dct[fromstring][tostring] += 1

def EventCounts(innings,dct):
    NI = len(innings) # number of innings
    for i in range(NI):
        fromstring = innings[i][0]
        for j in range(1,len(innings[i])):
            tostring = innings[i][j]
            AddEvent(fromstring,tostring,dct)
            fromstring = tostring

# ############################################
# BUilding the HMM

def GetCounts(mydir):
    games = GetGames(mydir)
    dct = {}
    for i in range(len(games)):
        outs, onbase = GetOutsBases(games[i])
        innings = ToInnings(outs,onbase)
        #print(games[i],len(outs))
        print('.', end='')
        EventCounts(innings,dct)
    return dct
#dct = GetCounts(mydir)

# convert the dictionary to probabilities
def ToProbs(dct):
    probs = copy.deepcopy( dct )
    for k in probs.keys():
        # sum of all entries
        sm = 0
        for k2 in probs[k].keys():
            sm += probs[k][k2]
        # probbilities
        for k2 in probs[k].keys():
            probs[k][k2] = probs[k][k2] / sm
    return probs

def EventProbs(trail,probs):
    p = 1
    for t in range(len(trail)-1):
        p *= probs[trail[t]][trail[t+1]]
    return p
# nat 7th inning WS game 7
#trail = ('0---','1---','1---','11--','1---','11--','112-','212-','3---')
# print( EventProbs(trail,probs))

# convert to log-odds
# each dictionary entry has a differen number of possible events.
def ToLogOdds(probs):
    logodds = copy.deepcopy( probs )
    for i in logodds.keys():
        L = len(logodds[i])
        for j in logodds[i].keys():
            logodds[i][j] = math.log( logodds[i][j]*L )
    return logodds

# rare innings - multiple from same game
def CompleteDict(games):
    dct = {}
    for game in games:
        outs, onbase = GetOutsBases(game)
        innings = ToInnings(outs,onbase)
        EventCounts(innings,dct)
    probs = ToProbs(dct)
    logodds = ToLogOdds(probs)
    return dct, probs, logodds

# ########################################
# functions for a season            
def GetGames(mydir):
    a = os.listdir(mydir)
    games = []
    for i in a:
        if '.shtml' in i:
            games.append(mydir+'/'+i)
    return games

def TrailLogOdds( trail, logodds ):
    p = 0
    N = len(trail)-1
    for t in range(N):
        p += logodds[trail[t]][trail[t+1]]
    return p/N

def InningsLogOdds(innings,logodds):
    answ = []
    NI = len(innings) # number of innings
    for i in range(NI):
        #print(innings[i])
        answ.append(TrailLogOdds(innings[i],logodds))
    return answ

# Find the strangest inning:  Lowest logodds
def SingleGameLowestInning(innings,logodds):
    lo, lid = 10,-1
    for i in range(len(innings)):
        a = TrailLogOdds(innings[i],logodds)
        if a < lo:
            lo = a
            lid = i
            oddinn = copy.deepcopy(innings[i])
    return lid, lo, oddinn


def RareInnings(games,logodds):
    data = []
    for game in games:
        outs, onbase = GetOutsBases(game)
        innings = ToInnings(outs,onbase)
        for i in range(len(innings)):
            a = TrailLogOdds(innings[i],logodds)
            data.append((a,i,game))
    # sort
    vec = np.array(list(map(lambda x:x[0],data)))
    ag = vec.argsort()
    answ = []
    for i in ag:
        answ.append(data[i])
    return answ

# #################################################
# Tracking players in games
# snarfing players and position
def GetNames(fname):
    with open(fname) as f:
        page = f.read()
    loc = page.find('id="KansasCityAthleticsbatting"')
    loc2 = page.find('<tbody>',loc)
    end = page.find('</tbody>',loc2)
    chunk = page[loc2:end]
    print(loc2,end,len(chunk))
    answ = []
    loc2=0
    for i in range(100):
        loc3 = chunk.find('th scope="row"',loc2)
        if loc3==-1:
            break
        loc4a = chunk.find('append-csv="',loc3)+12
        loc4b = chunk.find('"',loc4a)
        x = chunk[loc4a:loc4b]
        st = x+'.shtml">'
        loc5a = chunk.find(st,loc4b)+len(st)
        loc5b = chunk.find('</a>',loc5a)
        loc5c = chunk.find('</th>',loc5b)
        name = chunk[loc5a:loc5b]
        pos = chunk[loc5b+5:loc5c]
        answ.append((name,pos))
        loc6 = chunk.find('</tr>',loc5c)
        loc2=loc6+1
    return answ
    
#%%
def GetDate(fname):
    with open(fname) as f:
        page = f.read()
    loc1 = page.find('<strong>Attendance')
    loc2 = page.find('<div>',loc1-100)
    loc3a = page.find(',',loc2)
    loc3b = page.find('</',loc3a)
    dat = page[loc3a+2:loc3b]
    dat = dat.replace(',','')
    return dat

#%%
def PlayersInDct(fname,dct):
    players = GetNames(fname)
    dat = GetDate(fname)
    for i in players:
        name,pos = i
        if name not in dct:
            d = {}
            d[dat] = pos
            dct[name] = d
        else:
            dct[name][dat] = pos
