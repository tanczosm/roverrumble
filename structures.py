#!/usr/bin/env python
# This Python file uses the following encoding: utf-8
#import cgi
import datetime
#import wsgiref.handlers
try:
    import json
except:
    import simplejson as json
#import string
#import time
import zlib

import cPickle as pickle

from google.appengine.ext import db
#from google.appengine.api import users
#from google.appengine.ext import webapp

total = "TOTAL"
participants = "PARTICIPANTS"
sync = "SYNCHRONIZE"
allowed_clients = ["1.9.2.3"]
allowed_versions = ["1"]

global_dict = {}

class ComparePair:
    def __init__ (self, bota, botb):
        self.Name = bota.Name
        self.A_APS = bota.APS
        self.B_APS = botb.APS
        self.A_Survival = bota.Survival
        self.B_Survival = botb.Survival
        self.Diff_APS = self.A_APS - self.B_APS
        self.Diff_Survival = self.A_Survival - self.B_Survival
        self.A_Battles = bota.Battles
        self.B_Battles = botb.Battles
        self.A_LastUpload = bota.LastUpload
        self.B_LastUpload = botb.LastUpload
        

class ScoreSet:
    def __init__ (self, name = "", aps = 0.0, min_aps = 100.0, survival = 0.0, battles = 0, lastUpload = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")):
        self.Name = name
        self.APS = aps
        self.Min_APS = min_aps
        self.Survival = survival
        self.Battles = battles
        self.LastUpload = lastUpload
        self.KNNPBI = 0
        self.NPP = -1
        self.Alive = True
        
class LiteBot:
    def __init__ (self, bot = None, loadDict = None):
        if bot is not None:
            self.Name = bot.Name
            self.Battles = bot.Battles
            self.Pairings = bot.Pairings
            self.APS = bot.APS
            self.Survival = bot.Survival
            self.PL = bot.PL
            self.VoteScore = bot.VoteScore
            self.Rumble = bot.Rumble
            self.LastUpload = bot.LastUpload
            self.Active = bot.Active
            self.ANPP = bot.ANPP
            self.Uploaders = bot.__dict__.get("Uploaders",[])
        
        if loadDict is not None:
            self.__dict__.update(loadDict)
            
class CachedBotEntry:
    def __init__(self,bot):
        self.key_name = bot.key().name()
        self.Name = bot.Name
        self.Battles = bot.Battles
        self.Pairings = bot.Pairings
        self.APS = bot.APS
        self.Survival = bot.Survival
        self.PL = bot.PL
        self.VoteScore = bot.VoteScore
        self.Rumble = bot.Rumble
        self.LastUpload = bot.LastUpload
        self.Active = bot.Active
        self.PairingsList = bot.PairingsList
        self.ANPP = bot.ANPP
        self.Uploaders = bot.__dict__.get("Uploaders",[])
        
class BotEntry(db.Model):
    def init_from_cache(self,bot):
#        self.key_name = bot.key_name
        self.Name = bot.Name
        self.Battles = int(bot.Battles)
        self.Pairings = int(bot.Pairings)
        self.APS = float(bot.APS)
        self.Survival = float(bot.Survival)
        self.PL = int(bot.PL)
        self.VoteScore = float(bot.VoteScore)
        self.Rumble = bot.Rumble
        self.LastUpload = bot.LastUpload
        self.Active = bot.Active
        self.PairingsList = bot.PairingsList
        self.ANPP = float(bot.ANPP)
        self.Uploaders = bot.__dict__.get("Uploaders",[])
        
    #NR = db.StringProperty() --> key_name
    Name = db.StringProperty(indexed = False)
    Battles = db.IntegerProperty(indexed = False)
    Pairings = db.IntegerProperty(indexed = False)
    APS = db.FloatProperty(indexed = False)
    Survival = db.FloatProperty(indexed = False)
    PL = db.IntegerProperty(indexed = False)
    VoteScore = db.FloatProperty(indexed = False,default = 0.0)
    Rumble = db.StringProperty(indexed = False)
    LastUpload = db.StringProperty(indexed = False)
    Active = db.BooleanProperty(indexed = False)
    PairingsList = db.BlobProperty(indexed = False)
    ANPP = db.FloatProperty(indexed = False, default = 0.0)
    Uploaders = db.StringListProperty(indexed = False) 
    
    
#class Uploader(db.Model):
#    #NC = db.StringProperty() --> key_name
#    Name = db.StringProperty(indexed = False)
#    Client = db.StringProperty(indexed = False)
#    LastUpload = db.DateTimeProperty(indexed = False)
#    TotalUploads = db.IntegerProperty(indexed = False)
class User:
    def __init__(self,name,total=1,latest=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")):
        self.name = name
        self.total = total
        self.latest = latest
    
class Rumble(db.Model):
    #NRFTM = db.StringProperty() --> key_name
    Teams = db.BooleanProperty(indexed = False)
    Melee = db.BooleanProperty(indexed = False)
    MeleeSize = db.IntegerProperty(indexed = False)
    Rounds = db.IntegerProperty(indexed = False)
    Field = db.StringProperty(indexed = False)
    Name = db.StringProperty(indexed = False) # key_name
    TotalUploads = db.IntegerProperty(indexed = False)
    Participants = db.StringListProperty(indexed = False) 
    AvgBattles = db.FloatProperty(indexed = False, default = 0.0)
    LastUpload = db.StringProperty(indexed = False)
    PriorityBattles = db.BooleanProperty(indexed = False, default = True)
    BatchScoresAccurate = db.BooleanProperty(default = False)
    ParticipantsScores = db.BlobProperty(default = db.Blob(zlib.compress(pickle.dumps({}))), indexed = False)
    Uploaders = db.BlobProperty(indexed = False, default = db.Blob(zlib.compress(pickle.dumps({}))))
    
default_flag_map = "FLAGMAP"
allowed_flags = set(['ABW', 'AFG', 'AGO', 'AIA', 'ALA', 'ALB', 'AND', 'ARE', 
                     'ARG', 'ARM', 'ASM', 'ATA', 'ATF', 'ATG', 'AUS', 'AUT', 
                     'AZE', 'ANK', 'BDI', 'BLR', 'BRA', 'CAN', 'CHE', 'CHN', 
                     'CZE', 'DEU', 'ESP', 'FIN', 'FRA', 'GBR', 'GRC', 'HUN', 
                     'IRL', 'ITA', 'JPN', 'KOR', 'LTU', 'LVA', 'MAN', 'NLD', 
                     'NOR', 'NZL', 'POL', 'PRT', 'RUS', 'SGP', 'SRB', 'SWE', 
                     'SVK', 'THA', 'USA', 'VEN', 'WIKI', 'ZAF'])

class FlagMap(db.Model):
    #key_name is ALWAYS FLAGMAP
    InternalMap = db.BlobProperty(indexed = False, default = db.Blob(zlib.compress(pickle.dumps({}))))



# USAGE:
#    html_header % (Title, PageTitleHeader)
html_header = """<!DOCTYPE html><html><head><meta charset="utf-8"><title>LiteRumble - %s</title><link rel="stylesheet" type="text/css" media="all" href="style.css" /></head><body><h3>%s</h3>"""


country_lookup = {
 "NONE" : "Unknown",
 "MAN" : "Unknown",
 "WIKI": "Unknown",
 "AFG" : "Afghanistan",
 "AGO" : "Angola",
 "AIA" : "Anguilla",
 "ALA" : "Åland Islands",
 "ALB" : "Albania",
 "AND" : "Andorra",
 "ARE" : "United Arab Emirates",
 "ARG" : "Argentina",
 "ARM" : "Armenia",
 "ASM" : "American Samoa",
 "ATA" : "Antarctica",
 "ATF" : "French Southern and Antarctic Lands",
 "ATG" : "Antigua and Barbuda",
 "AUS" : "Australia",
 "AUT" : "Austria",
 "AZE" : "Azerbaijan",
 "BDI" : "Burundi",
 "BEL" : "Belgium",
 "BEN" : "Benin",
 "BES" : "Caribbean Netherlands",
 "BFA" : "Burkina Faso",
 "BGD" : "Bangladesh",
 "BGR" : "Bulgaria",
 "BHR" : "Bahrain",
 "BHS" : "The Bahamas",
 "BIH" : "Bosnia and Herzegovina",
 "BLM" : "Saint Barthélemy",
 "BLR" : "Belarus",
 "BLZ" : "Belize",
 "BMU" : "Bermuda",
 "BOL" : "Bolivia",
 "BRA" : "Brazil",
 "BRB" : "Barbados",
 "BRN" : "Brunei",
 "BTN" : "Bhutan",
 "BVT" : "Bouvet Island",
 "BWA" : "Botswana",
 "CAF" : "Central African Republic",
 "CAN" : "Canada",
 "CCK" : "Cocos Islands",
 "CHE" : "Switzerland",
 "CHL" : "Chile",
 "CHN" : "China",
 "CIV" : "Côte d'Ivoire",
 "CMR" : "Cameroon",
 "COD" : "Democratic Republic of the Congo",
 "COG" : "Republic of the Congo",
 "COK" : "Cook Islands",
 "COL" : "Colombia",
 "COM" : "Comoros",
 "CPV" : "Cape Verde",
 "CRI" : "Costa Rica",
 "CUB" : "Cuba",
 "CUW" : "Curaçao",
 "CXR" : "Christmas Island",
 "CYM" : "Cayman Islands",
 "CYP" : "Cyprus",
 "CZE" : "Czech Republic",
 "DEU" : "Germany",
 "DJI" : "Djibouti",
 "DMA" : "Dominica",
 "DNK" : "Denmark",
 "DOM" : "Dominican Republic",
 "DZA" : "Algeria",
 "ECU" : "Ecuador",
 "EGY" : "Egypt",
 "ERI" : "Eritrea",
 "ESH" : "Western Sahara",
 "ESP" : "Spain",
 "EST" : "Estonia",
 "ETH" : "Ethiopia",
 "FIN" : "Finland",
 "FJI" : "Fiji",
 "FLK" : "Falkland Islands",
 "FRA" : "France",
 "FRO" : "Faroe Islands",
 "FSM" : "Federated States of Micronesia",
 "GAB" : "Gabon",
 "GBR" : "United Kingdom",
 "GEO" : "Georgia",
 "GGY" : "Guernsey",
 "GHA" : "Ghana",
 "GIB" : "Gibraltar",
 "GIN" : "Guinea",
 "GLP" : "Guadeloupe",
 "GMB" : "Gambia",
 "GNB" : "Guinea-Bissau",
 "GNQ" : "Equatorial Guinea",
 "GRC" : "Greece",
 "GRD" : "Grenada",
 "GRL" : "Greenland",
 "GTM" : "Guatemala",
 "GUF" : "French Guiana",
 "GUM" : "Guam",
 "GUY" : "Guyana",
 "HKG" : "Hong Kong",
 "HMD" : "Heard Island and McDonald Islands",
 "HND" : "Honduras",
 "HRV" : "Croatia",
 "HTI" : "Haiti",
 "HUN" : "Hungary",
 "IDN" : "Indonesia",
 "IMN" : "Isle of Man",
 "IND" : "India",
 "IOT" : "British Indian Ocean Territory",
 "IRL" : "Republic of Ireland",
 "IRN" : "Iran",
 "IRQ" : "Iraq",
 "ISL" : "Iceland",
 "ISR" : "Israel",
 "ITA" : "Italy",
 "JAM" : "Jamaica",
 "JEY" : "Jersey",
 "JOR" : "Jordan",
 "JPN" : "Japan",
 "KAZ" : "Kazakhstan",
 "KEN" : "Kenya",
 "KGZ" : "Kyrgyzstan",
 "KHM" : "Cambodia",
 "KIR" : "Kiribati",
 "KNA" : "Saint Kitts and Nevis",
 "KOR" : "South Korea",
 "KWT" : "Kuwait",
 "LAO" : "Laos",
 "LBN" : "Lebanon",
 "LBR" : "Liberia",
 "LBY" : "Libya",
 "LCA" : "Saint Lucia",
 "LIE" : "Liechtenstein",
 "LKA" : "Sri Lanka",
 "LSO" : "Lesotho",
 "LTU" : "Lithuania",
 "LUX" : "Luxembourg",
 "LVA" : "Latvia",
 "MAC" : "Macau",
 "MAF" : "Collectivity of Saint Martin",
 "MAR" : "Morocco",
 "MCO" : "Monaco",
 "MDA" : "MoldovaMoldova, Republic of",
 "MDG" : "Madagascar",
 "MDV" : "Maldives",
 "MEX" : "Mexico",
 "MHL" : "Marshall Islands",
 "MKD" : "Macedonia",
 "MLI" : "Mali",
 "MLT" : "Malta",
 "MMR" : "Myanmar",
 "MNE" : "Montenegro",
 "MNG" : "Mongolia",
 "MNP" : "Northern Mariana Islands",
 "MOZ" : "Mozambique",
 "MRT" : "Mauritania",
 "MSR" : "Montserrat",
 "MTQ" : "Martinique",
 "MUS" : "Mauritius",
 "MWI" : "Malawi",
 "MYS" : "Malaysia",
 "MYT" : "Mayotte",
 "NAM" : "Namibia",
 "NCL" : "New Caledonia",
 "NER" : "Niger",
 "NFK" : "Norfolk Island",
 "NGA" : "Nigeria",
 "NIC" : "Nicaragua",
 "NIU" : "Niue",
 "NLD" : "Netherlands",
 "NOR" : "Norway",
 "NPL" : "Nepal",
 "NRU" : "Nauru",
 "NZL" : "New Zealand",
 "OMN" : "Oman",
 "PAK" : "Pakistan",
 "PAN" : "Panama",
 "PCN" : "Pitcairn IslandsPitcairn",
 "PER" : "Peru",
 "PHL" : "Philippines",
 "PLW" : "Palau",
 "PNG" : "Papua New Guinea",
 "POL" : "Poland",
 "PRI" : "Puerto Rico",
 "PRK" : "North Korea",
 "PRT" : "Portugal",
 "PRY" : "Paraguay",
 "PSE" : "Palestine",
 "PYF" : "French Polynesia",
 "QAT" : "Qatar",
 "REU" : "Réunion",
 "ROU" : "Romania",
 "RUS" : "Russia",
 "RWA" : "Rwanda",
 "SAU" : "Saudi Arabia",
 "SDN" : "Sudan",
 "SEN" : "Senegal",
 "SGP" : "Singapore",
 "SGS" : "South Georgia and the South Sandwich Islands",
 "SHN" : "Saint Helena, Ascension and Tristan da Cunha",
 "SJM" : "Svalbard and Jan Mayen",
 "SLB" : "Solomon Islands",
 "SLE" : "Sierra Leone",
 "SLV" : "El Salvador",
 "SMR" : "San Marino",
 "SOM" : "Somalia",
 "SPM" : "Saint Pierre and Miquelon",
 "SRB" : "Serbia",
 "SSD" : "South Sudan",
 "STP" : "São Tomé and Príncipe",
 "SUR" : "Suriname",
 "SVK" : "Slovakia",
 "SVN" : "Slovenia",
 "SWE" : "Sweden",
 "SWZ" : "Swaziland",
 "SXM" : "Sint Maarten",
 "SYC" : "Seychelles",
 "SYR" : "Syria",
 "TCA" : "Turks and Caicos Islands",
 "TCD" : "Chad",
 "TGO" : "Togo",
 "THA" : "Thailand",
 "TJK" : "Tajikistan",
 "TKL" : "Tokelau",
 "TKM" : "Turkmenistan",
 "TLS" : "East Timor",
 "TON" : "Tonga",
 "TTO" : "Trinidad and Tobago",
 "TUN" : "Tunisia",
 "TUR" : "Turkey",
 "TUV" : "Tuvalu",
 "TWN" : "Taiwan",
 "TZA" : "Tanzania",
 "UGA" : "Uganda",
 "UKR" : "Ukraine",
 "UMI" : "United States Minor Outlying Islands",
 "URY" : "Uruguay",
 "USA" : "United States",
 "UZB" : "Uzbekistan",
 "VAT" : "Vatican City",
 "VCT" : "Saint Vincent and the Grenadines",
 "VEN" : "Venezuela",
 "VGB" : "British Virgin Islands",
 "VIR" : "United States Virgin Islands",
 "VNM" : "Vietnam",
 "VUT" : "Vanuatu",
 "WLF" : "Wallis and Futuna",
 "WSM" : "Samoa",
 "YEM" : "Yemen",
 "ZAF" : "South Africa",
 "ZMB" : "Zambia",
 "ZWE" : "Zimbabwe"
}