#!/usr/bin/env python

import sys
sys.path.insert(0, 'libs')
import webapp2
import re
import glob
import os
import codecs
from google.appengine.ext import ndb
from google.appengine.ext import blobstore
from google.appengine.api import users
from google.appengine.ext.webapp import blobstore_handlers
import logging
import headers
import api

from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO) # dev_appserver.py --log_level debug .
log = logging.getLogger(__name__)

treeline = ""
HelpCache = {}

schemaText = '''<h2>Schema Structure</h2>

<p>The schema described on this site have been assembled to reflect <a href="http://bibliograph.net/docs/principles.html">shared principles</a> and the core types and properties are as defined by <a href="http://Schema.org">Schema.org</a>. The Editor of BiblioGraph.net will track changes to the published terms from Schema.org and update this site to reflect them.</p>

<p>When appropriate terms are not available in Schema.org, proposals from the <a href="http://www.w3.org/community/schemabibex/">Schema Bib Extend W3C Community Group</a> are looked to for suitable options. Finally, terms are added to the BiblioGraph.net namespace, often with acknowledgement of examples from other suitable vocabularies such as Dublin Core, Bibo, etc. The  goal is to keep the number of namespaces in BiblioGraph.net described data to a minimum with a preference for only two--schema: & bgn:</p>
<p>
The terms on this site are defined in rdfa source files, which are directly accessible:
<ul>
	<li>Core Schema.org vocabulary: <a href="/docs/schema_org_rdfa.html">/docs/schema_org_rdfa.html</a></li>
	<li>BiblioGraph.net terms: <a href="/docs/bibliograph_net_rdfa.html">/bibliograph_net_rdfa.html</a></li>
</ul>
</p>
'''

class MainPage(webapp2.RequestHandler):

	def write(self, str):
		self.outputStrings.append(str)
		
	def getTypeList(self):
		# initialize schema file, path, output string
		schema_domain = "http://bibliograph.net/"
		schema_name = "bgn"
		schema_file = "data/" + schema_name + ".rdfa"
		outstring = ""
		# if the schema file is found
		if os.path.isfile(schema_file):
			outstring += "<ul class=\"list-group\">"
			# create a dom object
			dom = BeautifulSoup(open(schema_file))
			# get divs in the dom
			for div in dom.find_all('div'):
				# if the div is for a class
				if div['typeof'] == "rdfs:Class":
					# if the schema domain is in the resource string 
					if schema_domain in div['resource']:
						# show the resource name
						r_label = div['resource'][div['resource'].rfind("/")+1:]
						outstring += "<li class=\"list-group-item\"><a href=\"/"+r_label+"\" class=\"prefix-"+schema_name+"\">"+r_label+"</a></li>"
		outstring += "</ul>"
		return outstring
		
	def showType(self,class_name,depth,maxdepth,showProperties=True):
		my_schema_prefix = self.getSchemaPrefixOfResource(class_name)
		class_str = ""
		Types = HelpCache.get('Types')
		if Types.get(class_name):
			multi = ""
			if len(Types[class_name]['subClassOf']) > 1:
				multi = " *"
			class_str = "<tr>"
			if depth > 0:
				for num in range(0,depth):
					class_str += "<td class=\"th_spacer\"></td>";
			class_str += "<td class=\"th_value\" "
			colspan = maxdepth - depth
			if colspan > 0:
				class_str += "colspan=\""+str(colspan)+"\""
			class_str += ">"
			class_str += "<a href=\"/"+Types[class_name]['label']+"\" class=\"prefix-"+my_schema_prefix+"\">"+Types[class_name]['label']+"</a>" + multi
			if showProperties:
				if len(Types[class_name]['properties']) > 0:
					class_str += ": "
					propinc = 0
					Types[class_name]['properties'].sort()
					for prop in Types[class_name]['properties']:
						my_schema_prop_prefix = self.getSchemaPrefixOfResource(prop)
						prop = prop[prop.rfind("/")+1:]
						if propinc > 0:
							class_str += ", "
						class_str += "<span class=\"prefix-"+my_schema_prop_prefix+"\">"+prop+"</span>"
						propinc = propinc+1
			class_str += "</td>"
			class_str += "</tr>\n"
		return class_str
		
	def getSchemaPrefixOfResource(self,res):
		schema_prefix = "unknown"
		schema_prefix = res[res.find('//')+2:]
		schema_prefix = schema_prefix[0:schema_prefix.find(".")]
		return schema_prefix
		
	def getVerFromDom(self,dom):
		for p in dom.find_all('p'):
			for span in p.find_all('span'):
				if span.get('property'):
					if span['property'] == "schema:softwareVersion":
						api.Unit.storeVersion(span.string)

	def getTypesAndTree(self):
		class_divs = {}
		Tree = {}
		Types = {}
		for schema_name in glob.glob("data/*.rdfa"):
				log.info("File: " + schema_name)
				dom = BeautifulSoup(open(schema_name))
				self.getVerFromDom(dom)
				# get the Types
				for div in dom.find_all("div",typeof="rdfs:Class"):
					class_div = div
					class_resource = div['resource']
					class_label = ""
					class_comment = ""
					class_subclassof = []
					class_properties = [] 
					class_divs[div['resource']] = class_div
						
					for s in class_div.find_all('span'):
						if s.get('property'):
							if s['property'] == "rdfs:comment":
								class_comment = s.string
							elif s['property'] == "rdfs:label":
								class_label = s.string
								if ":" in class_label:
									class_label = class_label[class_label.find(":")+1:]
						else:
							if s.a['property'] == "rdfs:subClassOf":
								class_subclassof.append(s.a['href'])
					
					class_dict = {'label': class_label, 'comment': class_comment, 'subClassOf': class_subclassof, 'properties': []}
					if Types.get(class_resource):
						# the class dictionary already has an entry for this resource.	
						# Update its comment if it's empty
						if not "comment" in Types[class_resource] and len(class_comment) > 0:
							Types[class_resource]['comment'] = class_comment
						# Update its subclass list
						if not Types[class_resource]['subClassOf']:
							Types[class_resource]['subClassOf'] = class_subclassof
						else:
							Types[class_resource]['subClassOf'] = Types[class_resource]['subClassOf'] + class_subclassof
					else:
						Types[class_resource] = class_dict
#					log.info(" "+class_label + str(len(Types[class_resource]['subClassOf'])))
					# add it as a child to its parents
					if not Tree.get(class_resource):
						Tree[class_resource] = []
					for sc in class_subclassof:
						if Tree.get(sc): 
							if Tree[sc].count(class_resource) == 0:
								Tree[sc].append(class_resource)
						else:
							Tree[sc] = []
							Tree[sc].append(class_resource)
							
				# get the properties
				for div in dom.find_all("div",typeof="rdfs:Property"):
					prop_div = div
					prop_resource = div['resource']
					prop_label = ""
					prop_comment = ""
					prop_domainIncludes = []
					prop_rangeIncludes = []
					for s in prop_div.find_all('span'):
						if s.get('property'):
							if s['property'] == "rdfs:comment":
								prop_comment = s.string
							elif s['property'] == "rdfs:label":
								prop_label = s.string
								if ":" in prop_label:
									prop_label = prop_label[prop_label.find(":")+1:]
						else:
							if s.a['property'] == "http://schema.org/domainIncludes":
								prop_domainIncludes.append(s.a['href'])
							elif s.a['property'] == "http://schema.org/rangeIncludes":
								prop_rangeIncludes.append(s.a['href'])
					
					# add this property to the properties list for the class identified as the range
					for r in prop_domainIncludes:
						if Types.get(r):
							Types[r]['properties'].append(prop_resource)
						else:
							r_label = r[r.rfind("/")+1:]
							class_dict = {'label': r_label, 'comment': '', 'subClassOf': '', 'properties': [prop_resource]}
							Types[r] = class_dict
				
		HelpCache['Tree'] = Tree
		HelpCache['Types'] = Types

	def get(self, node):

		helpTypeList = {}
		helpTypeList["schemas"] = "Browse the Schemas"
		helpTypeList["types"] = "The Type Hierarchy"
		if not node in helpTypeList:
			helpTypeList[node] = "Page Not Found"
			
		def walkTree(start=None, depth=0, showProperties=True):
			global treeline
			treeline += self.showType(start,depth,6,showProperties)
			Tree = HelpCache.get('Tree')
			if Tree.get(start):
				if len(Tree[start]) > 0:
					depth = depth+1
					Tree[start].sort()
					for leaf in Tree[start]:
						if len(Tree[leaf]) > 0:
							walkTree(leaf, depth, showProperties)
						else:
							treeline += self.showType(leaf,depth,6,showProperties)
					depth = depth-1
		
		self.outputStrings = []
		self.response.headers['Content-Type'] = 'text/html'
		hdr = headers.headers % ('', '', '', '', '', '', '')
		title = "Schemas"
		if(node == "types"):
			title = "Schemas- Full Hierarchy"
		hdr = hdr.replace("<title>", "<title>%s" % title)
		hdr = hdr.replace("<li><a href=\"/schemas\" >","<li class=\"active\"><a href=\"/schemas\" >")
		self.response.out.write(hdr)
		
		if node == "schemas":
			self.response.out.write(schemaText)
			self.response.out.write("<h2>"+helpTypeList[node]+"</h2>")
			self.response.out.write("<ul class=\"list-group\">")
			self.response.out.write("<li class=\"list-group-item\"><a href=\"Thing\">Starting at the top, one page per type</a></li>")
			self.response.out.write("<li class=\"list-group-item\"><a href=\"types\">Full list of types</a></li>")
			self.response.out.write("</ul>")
			self.response.out.write("<h2>BiblioGraph.net types:</h2>")
			self.response.out.write(self.getTypeList())
			
		elif node == "types":
			self.response.out.write("<h1>"+helpTypeList[node]+"</h1>")
			self.response.out.write("<em>* Indicates a Type with multiple parent Types</em>")
			global treeline
			if not HelpCache.get('Tree'):
				logging.debug("HelpCache MISS: Tree")
				self.getTypesAndTree()
			self.response.out.write("<table class=\"type-table\">\n")
			if not HelpCache.get('DataType'):
				treeline = ""
				walkTree("http://schema.org/DataType",0,True)
				HelpCache['DataType'] = treeline
			self.response.out.write(HelpCache['DataType'])
			self.response.out.write("</table>\n")
			self.response.out.write("<table class=\"type-table\">\n")
			if not HelpCache.get('Thing'):
				treeline = ""
				walkTree("http://schema.org/Thing",0,True)
				HelpCache['Thing'] = treeline
			self.response.out.write(HelpCache.get('Thing'))
			self.response.out.write("</table>\n")
		
		else:
			self.error(404)
			self.response.out.write("<h3>Sorry, the page you requested isn't available.</h2>")
			self.response.out.write("<h3>You can <a href='/schemas'>browse the Schemas page </a> as a way to get started using the site.</h3>")

		self.response.out.write("<br/><hr width='80%'/>")
		self.response.out.write(api.ShowUnit.getVersion())
		self.response.out.write(headers.footers)

app = ndb.toplevel(webapp2.WSGIApplication([("/(.*)", MainPage)]))