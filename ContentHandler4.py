# -*- coding: utf-8 -*-

import xml.sax

#ContentHandler for Template

'''
把attribute name和 后面的数字存在list里面
如果遇到和classname相同的标签
attributes 的下一行永远是attributeName
className: SECTOR
[
[SECTOR， {SECTORID: 0,
             SECNAME: sector_0,
             ANTAZIMUTH: 65535,
             SECTORANTENNA: 04000401}],      #含有<element>标签的，以attrName的colNum为基准，小于attrColNum的就记录进以当前attrName为key的value里面 
 [SFP, {CN: 0,
        SRN: 0,
        SN: 3,
        MODULEID: 0,
        PT: 8}],    #同一个classname重复多次, 看是否有同一个classname，找到下一个attribute标签，
]
'''
class ContentHandler(xml.sax.ContentHandler):

    def __init__(self, allTags, startTag, endTag):
        xml.sax.ContentHandler.__init__(self)
        # initialize your handler
        self.tag = ""
        self.fileList = []
        self.attrMap = {}
        self.withinAttribute = False
        self.lineNumOfClass = 50
        self.lineNumOfAttr = 0
        self.attrColNum = 0 #attributes所在的列
        self.attrNameColNum = 0 #attributes下一行的attribute 的具体name所在列
        self.attrMap = {}
        self.className = ""
        self.currAttrName = ""



    def startElement(self, name, attrs):
        #global fileList
        self.tag = name
        loc = self._locator
        line, col = loc.getLineNumber(), loc.getColumnNumber()
        #最后一个class是通过找到最下面的spec标签加入进去
        if line > self.lineNumOfClass and self.tag.startswith("spec"):
            self.fileList.append([[], []])
            self.fileList[len(self.fileList) - 1][0] = self.className
            self.fileList[len(self.fileList) - 1][1] = self.attrMap
            #print(self.fileList[len(self.fileList) - 1])
        if name == "class":
            self.lineNumOfClass = line
            self.withinAttribute = False
            if self.className != "":
                self.fileList.append([[], []])
                self.fileList[len(self.fileList) - 1][0] = self.className
                self.fileList[len(self.fileList) - 1][1] = self.attrMap
                #print(self.fileList[len(self.fileList) - 1])
            # fo.write(str(self.allTagStr) + "\n")

            self.className = ""
            self.attrMap = {}
        if line == self.lineNumOfClass + 1:
            self.className = name
        if name == "attributes":
            self.withinAttribute = True
            self.lineNumOfAttr = line
            self.attrColNum = col
        #获得attributeName所在列
        if line == self.lineNumOfAttr+1:
            self.attrNameColNum = col
        if col == self.attrNameColNum:
            self.currAttrName = name
        #print 'start of {} element at line {}, column {}'.format(name, line, col)


    def endElement(self, name):
        pass


    def characters(self, content):
        #global fileList, allTags, tagAndIdx
        if self.tag == self.currAttrName:
            if self.attrMap.__contains__(self.currAttrName):
                self.attrMap[self.currAttrName] += str(content.replace("\n","").replace(" ","").replace("\t",""))
            else:
                self.attrMap[self.currAttrName] = str(content.replace("\n","").replace(" ","").replace("\t",""))



if __name__ == "__main__":
    # 创建一个 XMLReader

    parser = xml.sax.make_parser()
    # turn off namepsaces
    parser.setFeature(xml.sax.handler.feature_namespaces, 0)

    # 重写 ContextHandler
    Handler = ContentHandler([], "", "")
    parser.setContentHandler(Handler)
    parser.parse("LO_old/Template/BTS3900_BBU3910_BTS3900_FDD_S1_2T2R.xml")
    #print(Handler.fileList)
'''
    Handler2 = ContentHandler([], "", "")
    parser.setContentHandler(Handler2)
    parser.parse("LO_new/BTS3900_BBU3910_BTS3900_FDD_S1_2T2R.xml")
    print(str(Handler2.fileList).decode("string_escape"))
'''

