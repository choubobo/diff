# -*- coding: utf-8 -*-

import xml.sax


class ContentHandler(xml.sax.ContentHandler):

    def __init__(self, allTags, startTag, endTag):
        xml.sax.ContentHandler.__init__(self)
        # initialize your handler
        self.tag = ""
        self.fileList = []
        self.allTags = allTags
        self.tagNum = len(self.allTags)
        self.tagAndIdx = {}
        self.block = []
        self.allTagStr = []
        self.startTag = startTag
        self.endTag = endTag
        for i in range(self.tagNum):
            self.tagAndIdx[self.allTags[i]] = i

        for i in range(self.tagNum):
            self.allTagStr.append("")
        #print("constructor ")
        #print(ContentHandler1.allTagStr)


    def startElement(self, name, attrs):
        #global fileList
        self.tag = name

        if name == self.startTag:
            self.block = []
            self.fileList.append(self.block)
            for attrsKey in self.allTags[0:4]:
                self.allTagStr[self.tagAndIdx.get(attrsKey)] = attrs[attrsKey]

        if name == "loop":
            for attrsKey in self.allTags[4:6]:
                #if attrs.has_key(attrsKey):
                if attrsKey in attrs.getNames():
                    self.allTagStr[self.tagAndIdx.get(attrsKey)] = attrs[attrsKey]
                else:
                    self.allTagStr[self.tagAndIdx.get(attrsKey)] = ""
        '''  
        loc = self._locator
        if loc is not None:
            line, col = loc.getLineNumber(), loc.getColumnNumber()
        else:
            line, col = 'unknown', 'unknown'
        print 'start of {} element at line {}, column {}'.format(name, line, col)
        '''

    def endElement(self, name):
        #global fo
        if name == self.endTag:
            for element in self.allTagStr:
                self.fileList[len(self.fileList) - 1].append(element.replace("\n","").replace(" ",""))

            #fo.write(str(self.allTagStr) + "\n")

            self.allTagStr = []
            for k in range(self.tagNum):
                self.allTagStr.append("")

    def characters(self, content):
        #global fileList, allTags, tagAndIdx
        if self.tag in self.allTags:
            #print(self.tag +" : "+ content)
            #print(str(self.allTagStr))
            #fo.write(str(self.allTagStr) + "\n")
            self.allTagStr[self.tagAndIdx.get(self.tag)] += content

'''
if __name__ == "__main__":
    # 创建一个 XMLReader

    parser = xml.sax.make_parser()
    # turn off namepsaces
    parser.setFeature(xml.sax.handler.feature_namespaces, 0)

    # 重写 ContextHandler
    Handler = ContentHandler()
    parser.setContentHandler(Handler)

    parser.parse("test/LO_SPC130/DEV_LTE.xml")

    print(str(Handler.fileList).decode("string_escape"))

'''
