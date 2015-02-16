#!/usr/bin/env python
#

import webapp2
import re
from google.appengine.ext import db
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
import xml.etree.ElementTree as ET
import logging

headers = '''<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    
    <title>%s - BiblioGraph.net</title>
    <meta name="description" content="BiblioGraph.net is a set of extensible schemas, with a bibliographic focus, that build on the capabilities of Schema.org 
    that enable webmasters to embed structured data on their web pages for use by search engines and other applications." />
    <link rel="icon" href="/assets/img/favicon.ico" type="image/x-icon"/>
    <link rel="shortcut icon" href="/assets/img/favicon.ico" type="image/x-icon"/>
    <link rel="stylesheet" type="text/css" href="/assets/bootstrap3/css/bootstrap.min.css" />
    <link rel="stylesheet" type="text/css" href="/docs/bibliograph.css" />
    <link rel="stylesheet" type="text/css" href="/docs/prettify.css" />
    <script type="text/javascript" src="/docs/prettify.js"></script>
    <script type="text/javascript" src="/assets/js/jquery.min.js"></script>

<script type="text/javascript">
      $(document).ready(function(){
        prettyPrint();
        setTimeout(function(){

  $(".atn:contains(itemscope), .atn:contains(itemtype), .atn:contains(itemprop), .atn:contains(itemid), .atn:contains(time), .atn:contains(datetime), .atn:contains(datetime), .tag:contains(time) ").addClass(\'new\');
  $('.new + .pun + .atv\').addClass(\'curl\');

        }, 500);
        setTimeout(function(){

  $(".atn:contains(property), .atn:contains(typeof) ").addClass(\'new\');
  $('.new + .pun + .atv\').addClass(\'curl\');

        }, 500);
        setTimeout(function() {
          $('.ds-selector-tabs .selectors a').click(function() {
            var $this = $(this);
            var $p = $this.parents('.ds-selector-tabs');
            $('.selected', $p).removeClass('selected');
            $this.addClass('selected');
            $('pre.' + $this.data('selects'), $p).addClass('selected');
          });
        }, 0);
      });
</script>

<style>

  .pln    { color: #444;    } /* plain text                 */
  .tag    { color: #515484; } /* div, span, a, etc          */
  .atn,
  .atv    { color: #314B17; } /* href, datetime             */
  .new    { color: #660003; } /* itemscope, itemtype, etc,. */
  .curl   { color: #080;    } /* new url                    */

  table.definition-table {
    border-spacing: 3px;
    border-collapse: separate;
  }

</style>

</head>
<body>
    <div class="container">
    <div class="row">
        <div class="col-md-6">
            <h1><a href="/" class="noborder"><span class="logo_dark">Biblio</span><span class="logo_light">Graph</span><span class="logo_dark">.net</span></a></h1>
        </div>
		
        <div class="col-md-6">
            <div class="pull-right">
                 <div id="cse-search-form" style="width: 400px;"></div>
            </div>
        </div>

		<script type="text/javascript" src="//www.google.com/jsapi"></script>
		<script type="text/javascript">
		  google.load(\'search\', \'1\', {language : \'en\', style : google.loader.themes.MINIMALIST});
		  google.setOnLoadCallback(function() {
		    var customSearchControl = new google.search.CustomSearchControl(\'014918374978744102058:-yfdgutyfb8\');
		    customSearchControl.setResultSetSize(google.search.Search.FILTERED_CSE_RESULTSET);
		    var options = new google.search.DrawOptions();
		    options.enableSearchboxOnly("/docs/search_results.html", null, false, \'#\');
		    customSearchControl.draw(\'cse-search-form\', options);
		    // over-ride gsc css with bootstrap css
		    $( "#gsc-i-id1" ).addClass( "form-control" );
		    $( "input[type='button']" ).removeClass( "gsc-search-button" ).addClass( "btn btn-success" );
		  }, true);
		</script>
    </div>

    <ul class="nav nav-tabs">
        <li><a href="/" >Home</a></li>
        <li><a href="/schemas" >Schemas</a></li>
        <li><a href="/docs/bgn_releases.html" >Releases</a></li>
        <li><a href="/docs/feedback.html" >Feedback</a></li>
    </ul>


  <div id="mainContent" vocab="%s" typeof="%s" resource="%s%s" %s>
  %s

'''

footers = '''</div>
<div id="footer"><a href="/docs/terms.html" class="noborder pull-right">BiblioGraph.net Terms and Conditions</a></div>
<script src="/assets/bootstrap3/js/bootstrap.min.js"></script>
</div>
</body>
</html>
'''

def OutputSchemaorgHeaders(webapp, vocab='http://schema.org/',entry='', is_class=False, extras='', ext_mappings=''):
    """
    Generates the headers for class and property pages

    * entry = name of the class or property
    """

    rdfs_type = 'rdfs:Property'
    if is_class:
        rdfs_type = 'rdfs:Class'
    out = headers % (str(entry), str(vocab), rdfs_type, str(vocab), str(entry), extras, ext_mappings)
    webapp.response.write(out)
