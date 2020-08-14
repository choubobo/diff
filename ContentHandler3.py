# -*- coding: utf-8 -*-

import xml.sax

#fo = open("print.txt","w")

#ContentHandler for OCL files
class ContentHandler(xml.sax.ContentHandler):
    def __init__(self, allTags, startTag, endTag):
        xml.sax.ContentHandler.__init__(self)
        # initialize your handler
        self.tag = ""
        self.fileList = []
        self.allTags1 = ["Id", "MOName", "NewRule", "OldRule", "Pdt", "ErrCode", "CRuleName", "ERuleName", "CRuleDesc", "ERuleDesc", "OclDesc", "NeCode", "OpType", "VerifyData", "Owner", "Comments"]
        self.allTags2 = ["ParaId", "MOName", "Type", "ParaName", "NewRule", "OldRule", "Pdt", "ErrCode", "RuleName", "RuleContent", "ERuleContent", "OCLDesc", "NeCode", "OpType", "VerifyData", "Owner", "Comments"]
        self.tagAndIdx1 = {}
        self.tagAndIdx2 = {}
        self.block = []
        self.allTagStr1 = []
        self.allTagStr2 = []
        self.startTag = startTag
        self.endTag = endTag
        self.isStartTagChange = False
        for i in range(len(self.allTags1)):
            self.tagAndIdx1[self.allTags1[i]] = i
        for i in range(len(self.allTags2)):
            self.tagAndIdx2[self.allTags2[i]] = i

        for i in range(len(self.allTags1)):
            self.allTagStr1.append("")
        for i in range(len(self.allTags2)):
            self.allTagStr2.append("")


    def startElement(self, name, attrs):
        #global fileList
        self.tag = name
        if name == "MO":
            self.isStartTagChange = False
            self.fileList.append([])

        if name == "Para":
            self.isStartTagChange = True
            self.fileList.append([])


    '''  
        loc = self._locator
        if loc is not None:
            line, col = loc.getLineNumber(), loc.getColumnNumber()
        else:
            line, col = 'unknown', 'unknown'
        print 'start of {} element at line {}, column {}'.format(name, line, col)
        '''


    def endElement(self, name):
        if name == self.endTag:
            if not self.isStartTagChange:
                for element in self.allTagStr1:
                    self.fileList[len(self.fileList) - 1].append(element)
                    #print(self.fileList[len(self.fileList) - 1])
                self.allTagStr1 = []
                for k in range(len(self.allTags1)):
                    self.allTagStr1.append("")
            else:
                for element in self.allTagStr2:
                    self.fileList[len(self.fileList) - 1].append(element)
                self.allTagStr2 = []
                for k in range(len(self.allTags2)):
                    self.allTagStr2.append("")


    def characters(self, content):
        #global fileList, allTags, tagAndIdx
        if not self.isStartTagChange:
            if self.tag in self.allTags1:
                self.allTagStr1[self.tagAndIdx1.get(self.tag)] += content
        else:
            if self.tag in self.allTags2:
                self.allTagStr2[self.tagAndIdx2.get(self.tag)] += content

'''
if __name__ == "__main__":
    # 创建一个 XMLReader

    parser = xml.sax.make_parser()
    # turn off namepsaces
    parser.setFeature(xml.sax.handler.feature_namespaces, 0)
    allTags = []
    startTag = ""
    endTag = "Comments"
    # 重写 ContextHandler
    Handler = ContentHandler(allTags, startTag, endTag)
    parser.setContentHandler(Handler)

    parser.parse("LO_SPC112/OCL/0_rosa_rb_config_rule_dev.xml")
    fo.write(str(Handler.fileList).decode("string_escape"))
    fo.close
'''

