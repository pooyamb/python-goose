# -*- coding: utf-8 -*-
"""\
This is a python port of "Goose" orignialy licensed to Gravity.com
under one or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.

Python port was written by Xavier Grangier for Recrutae

Gravity.com licenses this file
to you under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from HTMLParser import HTMLParser
from goose.text import innerTrim

class OutputFormatter(object):

    def __init__(self, config, article):
        # config
        self.config = config

        # article
        self.article = article

        # parser
        self.parser = self.config.get_parser()

        # stopwords class
        self.stopwords_class = config.stopwords_class

        # top node
        self.top_node = None

    def get_language(self):
        """\
        Returns the language is by the article or
        the configuration language
        """
        # we don't want to force the target laguage
        # so we use the article.meta_lang
        if self.config.use_meta_language == True:
            if self.article.meta_lang:
                return self.article.meta_lang[:2]
        return self.config.target_language

    def get_top_node(self):
        return self.top_node

    def do_formating(self):
        self.top_node = self.article.top_node
        self.remove_negativescores_nodes()
        self.links_to_text()
        self.replace_with_text()
    
    def get_formatted_text(self):
        self.add_newline_to_br()
        self.remove_fewwords_paragraphs()
        return self.convert_to_text()

    def get_formatted_html(self):
        self.remove_fewwords_paragraphs(True)
        self.remove_point_attrs()
        return self.top_node
    
    def is_image_box(self,e):
        image_box_attr = self.parser.getAttribute(e, "image_box")
        if image_box_attr is '1' :
            return True
        elif image_box_attr is '2' :
            return False
        return False

    def remove_point_attrs(self):
        # Get nodes with gravity_score attribute
        items = self.parser.css_select(self.top_node, "*[gravity_score]")
        for item in items :
            self.parser.delAttribute(item,'gravity_score')
            self.parser.delAttribute(item,'gravity_nodes')
            
        # Get nodes with image_box attribute
        items = self.parser.css_select(self.top_node, "*[image_box]")
        for item in items :
            self.parser.delAttribute(item,'image_box')
        
        
        items = self.parser.css_select(self.top_node, "*")
        for item in items :
            self.parser.delAttribute(item,'id')
            self.parser.delAttribute(item,'class')
            self.parser.delAttribute(item,'style')
            self.parser.delAttribute(item,'dir')
            

    def convert_to_text(self):
        txts = []
        for node in list(self.get_top_node()):
            txt = self.parser.getText(node)
            if txt:
                txt = HTMLParser().unescape(txt)
                txt_lis = innerTrim(txt).split(r'\n')
                txts.extend(txt_lis)
        return '\n\n'.join(txts)

    def add_newline_to_br(self):
        for e in self.parser.getElementsByTag(self.top_node, tag='br'):
            e.text = r'\n'

    def links_to_text(self):
        """\
        cleans up and converts any nodes that
        should be considered text into text
        """
        self.parser.stripTags(self.get_top_node(), 'a')

    def remove_negativescores_nodes(self):
        """\
        if there are elements inside our top node
        that have a negative gravity score,
        let's give em the boot
        """
        gravity_items = self.parser.css_select(self.top_node, "*[gravity_score]")
        for item in gravity_items:
            score = self.parser.getAttribute(item, 'gravity_score')
            score = int(score, 0)
            if score < 1:
                item.getparent().remove(item)

    def replace_with_text(self):
        """\
        replace common tags with just
        text so we don't have any crazy formatting issues
        so replace <br>, <i>, <strong>, etc....
        with whatever text is inside them
        code : http://lxml.de/api/lxml.etree-module.html#strip_tags
        """
        self.parser.stripTags(self.get_top_node(), 'b', 'strong', 'i', 'br', 'sup')

    def remove_fewwords_paragraphs(self, except_image = False):
        """\
        remove paragraphs that have less than x number of words,
        would indicate that it's some sort of link
        """
        all_nodes = self.parser.getElementsByTags(self.get_top_node(), ['*'])
        all_nodes.reverse()
        for el in all_nodes:
            tag = self.parser.getTag(el)
            text = self.parser.getText(el)
            stop_word_class = self.stopwords_class(language=self.get_language())
            stop_words = stop_word_class.get_stopword_count(text)
            min_stop_word_point = stop_word_class.min_stop_word_point
            condition = (tag != 'br' or text != '\\r') and stop_words.get_stopword_count() < min_stop_word_point \
                and len(self.parser.getElementsByTag(el, tag='object')) == 0 \
                and len(self.parser.getElementsByTag(el, tag='embed')) == 0
            if except_image :
                image_box = self.is_image_box(el)
                condition = condition and not (image_box or tag == 'img')
            if condition:
                self.parser.remove(el)
            # TODO
            # check if it is in the right place
            else:
                trimmed = self.parser.getText(el)
                if trimmed.startswith("(") and trimmed.endswith(")"):
                    self.parser.remove(el)

class StandardOutputFormatter(OutputFormatter):
    pass
