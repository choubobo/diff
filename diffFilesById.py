import install

install.intall_function()
import chardet
import difflib
import io
import re
import xml
import copy
import pandas as pd
import os
import ContentHandler1 as ch1
import ContentHandler2 as ch2
import ContentHandler3 as ch3
import ContentHandler4 as ch4

'''
用索引唯一的标识一个block
1. 把索引和内容放入list，一个一个对应着按顺序比较
    
    if id[0][i] == id[1][j]:
        compareContent(i,j)
        i++;
        j++;

    elif id[0][i] != id[1][j]:
        for k in range(1:):
            res = skipNLine(k);
            if(res == "删除" or res == "增加"):
                break


    skipNLine(k):
        if id[0][i+k] == id[0][j]
            return "删除"
        if id[0][i] == id[0][j+k]
            return "增加"
        else：
            return “没有匹配上”
'''

'''
优化的点：ScenList每一个block内部识别 不够准确
'''


class NoMatchedBlockId(BaseException):
    pass


#去掉空格 换行符
def stripAll(string):
    for sign in ["\n", "\t", " "]:
        string = str(string).replace(sign, "")
    string = str(string).replace("，",",")
    return string


#判断两个block的id是否一致
def isIdSame(IDIndex, i, j, fileList1, fileList2):
    for idx in IDIndex:
        # 曾经报错： 数组下标越界，当skipKline超过总长度
        if i < len(fileList1) and j < len(fileList2):
            if pd.isnull(fileList1[i][idx]) and pd.isnull(fileList2[j][idx]):
                continue
            if fileList1[i][idx] != fileList2[j][idx]:
                return False
        # 如果i,j下标越界，则没有匹配上
        else:
            return False
    return True


def skipKLine(IDIndex, fileList1, fileList2, i, j, k):
    if isIdSame(IDIndex, i + k, j, fileList1, fileList2):
        return "删除"
    elif isIdSame(IDIndex, i, j + k, fileList1, fileList2):
        return "增加"
    else:
        return "没有匹配上"


# 试着跳过k行看是否匹配
def skipKLineInExcel(fileList1, fileList2, i, j, k):
    len1 = len(fileList1)
    len2 = len(fileList2)
    if i + k < len1 and j < len2 and fileList1[i + k][0] == fileList2[j][0]:
        return "删除"
    elif i < len1 and j + k < len2 and fileList1[i][0] == fileList2[j + k][0]:
        return "增加"
    else:
        return "没有匹配上"


#把list存成map的形式，以index为key，其他内容为value
def turnListToMap(fileList, IDIndex):
    map = {}
    mapWithSpace = {}
    i = 0
    for row in fileList:
        try:
            re.search(r'\w', row[0])
        except:
            mapWithSpaceValue = row[1:]
            for idx in range(len(row)):
                row[idx] = stripAll(row[idx])
            map[row[0]] = row[1:]
            mapWithSpace[row[0]] = mapWithSpaceValue
        else:
            if re.search(r'\w', row[0]):  # 匹配匹配字母或数字或下划线或汉字
                mapWithSpaceValue = row[1:]
                for idx in range(len(row)):
                    row[idx] = stripAll(row[idx])
                map[row[0]] = row[1:]
                mapWithSpace[row[0]] = mapWithSpaceValue
            #print(map[row[0]])
    return map, mapWithSpace


def appendRowInDiffRes(id, map, diffRes, changeType):
    row = [changeType]
    row.extend([id])
    row.extend(map.get(id))
    diffRes.append(row)


def backUpDiffOCLDirByLine(fileList1, fileList2, IDIndex):
    diffRes = []
    map1, mapWithSpace1 = turnListToMap(fileList1, IDIndex)
    map2, mapWithSpace2 = turnListToMap(fileList2, IDIndex)
    idSet1 = set(map1.keys())
    idSet2 = set(map2.keys())
    deletedIds = idSet1 - idSet2
    addedIds = idSet2 - idSet1
    intersectIds = idSet1 & idSet2
    if deletedIds:
        for id in deletedIds:
            appendRowInDiffRes(id, mapWithSpace1, diffRes, "删除")
    if addedIds:
        for id in addedIds:
            appendRowInDiffRes(id, mapWithSpace2, diffRes, "增加")
    if intersectIds:
        for id in intersectIds:
            if map1[id] != map2[id]:
                appendRowInDiffRes(id, mapWithSpace1, diffRes, "修改前")
                appendRowInDiffRes(id, mapWithSpace2, diffRes, "修改后")
    return diffRes


# 单独处理OCL文件夹，因为xml文件的格式不一样
def diffOCLDirByLine(handler1, handler2, fileName):
    diffRes = []
    fileList1 = handler1.fileList
    fileList2 = handler2.fileList
    file1BlockNum = len(fileList1)
    file2BlockNum = len(fileList2)
    i, j = 0, 0

    while i < file1BlockNum and j < file2BlockNum:
        # 如果id为空，以前9个tag作为索引
        # fo.write(str(len(fileList1[i]))+"\n")
        if fileList1[i][0] == "":
            IDIndex = [0, 1, 2, 3, 4, 5, 6, 7, 8]
        else:
            IDIndex = [0]
        try:
            i, j, isEnd = diffALine(IDIndex, i, j, fileList1, fileList2, diffRes)
            if isEnd:
                break
        except NoMatchedBlockId:
            printExceptionResult(fileName, fileList1[i], fileList2[j])
            print("使用备用方案中。。。")
            # 使用map对比id
            diffRes = backUpDiffOCLDirByLine(fileList1, fileList2, [0])
            return diffRes
    # diffRes = backUpDiffOCLDirByLine(fileList1, fileList2)
    dealWithRemainedRows(i, len(fileList1), fileList1, diffRes, "删除")
    dealWithRemainedRows(j, len(fileList2), fileList2, diffRes, "增加")
    return diffRes


def printExceptionResult(fileName, list1, list2):
    print(str(fileName) + " 此文件找不到匹配的block id")
    #print("这两个block无法匹配：")
    #print(list1)
    #print(list2)


def diffALine(IDIndex, i, j, fileList1, fileList2, diffRes):
    # 同样的block ID
    isEnd = False
    if isIdSame(IDIndex, i, j, fileList1, fileList2):
        # 两个block内容不一样
        if not compareContent(fileList1, fileList2, i, j):
            row1 = copy.deepcopy(fileList1[i])
            row1.insert(0, "修改前")
            diffRes.append(row1)
            row2 = copy.deepcopy(fileList2[j])
            row2.insert(0, "修改后")
            diffRes.append(row2)
        i += 1
        j += 1
    # block id 不一样
    else:
        startI = i
        startJ = j
        i, j, isEnd = dealBlockIdDiff(i, j, fileList1, fileList2, IDIndex)
        # 在文档中间被删除或增加的
        dealWithRemainedRows(startI, i, fileList1, diffRes, "删除")
        dealWithRemainedRows(startJ, j, fileList2, diffRes, "增加")
    return i, j, isEnd


# 遍历完两边的文件夹剩下的几行
def dealWithRemainedRows(startI, endI, fileList, diffRes, changeType):
    for m in range(startI, endI):
        row1 = copy.deepcopy(fileList[m])
        row1.insert(0, changeType)
        diffRes.append(row1)


def appendHighDirRowInDiffRes(id, map, diffRes, changeType):
    row = []
    threeKeys = id.split("|")
    for i in range(0,14):
        row.append("")
    row[0] = threeKeys[0]
    row[1] = threeKeys[1]
    row[2] = map[id][0]
    row[3] = map[id][1]
    row[4] = threeKeys[2]
    for i in range(5,14):
        row[i] = map[id][i-3]
    row.insert(0,changeType)
    diffRes.append(row)


def backUpDiffHighDirByLine(fileList1,fileList2,IDIndex):
    diffRes = []
    map1 = turnHighDirListToMap(fileList1, IDIndex)
    map2 = turnHighDirListToMap(fileList2, IDIndex)
    idSet1 = set(map1.keys())
    idSet2 = set(map2.keys())
    deletedIds = idSet1 - idSet2
    addedIds = idSet2 - idSet1
    intersectIds = idSet1 & idSet2
    if deletedIds:
        for id in deletedIds:
            appendHighDirRowInDiffRes(id, map1, diffRes, "删除")
    if addedIds:
        for id in addedIds:
            appendHighDirRowInDiffRes(id, map2, diffRes, "增加")
    if intersectIds:
        for id in intersectIds:
            if map1[id] != map2[id]:
                appendHighDirRowInDiffRes(id, map1, diffRes, "修改前")
                appendHighDirRowInDiffRes(id, map2, diffRes, "修改后")
    return diffRes


def turnHighDirListToMap(fileList, IDIndex):
    map = {}

    for row in fileList:
        key = ""
        value = []
        for id in range(len(row)):
            if id in IDIndex:
                try:
                    curr = row[id] + "|"
                except:
                    curr = str(row[id],"utf-8") + "|"
                key += curr
            else:
                value.append(row[id])
        map[key] = value
    return map


#包括Assop high_risk_info Integrity文件夹里面的文件
def diffNormalDirByLine(IDIndex, handler1, handler2, fileName, subdir):
    diffRes = []
    fileList1 = handler1.fileList
    fileList2 = handler2.fileList
    i, j = 0, 0

    while i < len(fileList1) and j < len(fileList2):
        try:
            i, j, isEnd = diffALine(IDIndex, i, j, fileList1, fileList2, diffRes)
            if isEnd:
                break
        except NoMatchedBlockId:
            printExceptionResult(fileName, fileList1[i], fileList2[j])
            if subdir != "high_risk_info":
                print("备用方案启用中...")
                diffRes = backUpDiffOCLDirByLine(fileList1,fileList2,IDIndex)
            else:
                print("high_risk_info的备用方案启用中...")
                diffRes = backUpDiffHighDirByLine(fileList1,fileList2,IDIndex)
            return diffRes

    dealWithRemainedRows(i, len(fileList1), fileList1, diffRes, "删除")
    dealWithRemainedRows(j, len(fileList2), fileList2, diffRes, "增加")
    return diffRes


def compareContent(fileList1, fileList2, i, j):
    for k in range(len(fileList1[i])):
        if k >= len(fileList2[j]):
            return False
        if pd.isnull(fileList1[i][k]) and pd.isnull(fileList2[j][k]):
            continue
        row1 = fileList1[i][k]
        row2 = fileList2[j][k]
        try:
            stripAll(row1)
            stripAll(row2)
        except:
            #可能有byte型的需要先被转换
            if stripAll(str(row1, encoding="utf8")) != stripAll(str(row2, encoding="utf8")):
                return False
        else:
            if stripAll(row1) != stripAll(row2):
                return False
    return True


def writeToExcel(allDiffRes, allDiffFileNames, allTags, outPath, subdir):
    # from ContentHandler1 import allTags
    allTags.insert(0, "改变类型")
    # print(allTags)
    dataframes = []
    # OCL 文件夹内一个文件可能有两种标签类型，所以无法列出列名
    if subdir == "OCL":
        for diffRes in allDiffRes:
            dataframe = pd.DataFrame(diffRes)
            dataframes.append(dataframe)
    else:
        for diffRes in allDiffRes:
            dataframe = pd.DataFrame(diffRes, columns=allTags)
            dataframes.append(dataframe)

    i = 0
    with pd.ExcelWriter(outPath) as writer:
        for dataframe in dataframes:
            try:
                # print(dataframe)
                dataframe.to_excel(writer, sheet_name=allDiffFileNames[i])
                i += 1
            except:
                print("ERROR when used writeToExcel FUNCTION")


# 遍历0_CN_0_SRN_COMM文件 得到整个文件的diffRes
def diff0CNDirByLine(IDIndex, file1, file2, fileName):
    diffRes = []
    fileList1, fileList2 = getListFromCsv(file1, file2)
    file1BlockNum = len(fileList1)
    file2BlockNum = len(fileList2)
    i, j = 0, 0
    while i < file1BlockNum and j < file2BlockNum:
        try:
            i, j, isEnd = diffALine(IDIndex, i, j, fileList1, fileList2, diffRes)
            if isEnd:
                break
        except NoMatchedBlockId:
            printExceptionResult(fileName, fileList1[i], fileList2[j])
            return diffRes

    dealWithRemainedRows(i, len(fileList1), fileList1, diffRes, "删除")
    dealWithRemainedRows(j, len(fileList2), fileList2, diffRes, "增加")
    return diffRes


def getDiffRes(file1, file2, allTags, startTag, endTag, IDIndex, contentHandler, subdir):
    # from ContentHandler2 import ContentHandler2 as handler2
    parser = xml.sax.make_parser()
    # turn off namepsaces
    parser.setFeature(xml.sax.handler.feature_namespaces, 0)
    # 重写 ContextHandler
    Handler1 = contentHandler.ContentHandler(allTags, startTag, endTag)
    parser.setContentHandler(Handler1)
    parser.parse(file1)
    Handler2 = contentHandler.ContentHandler(allTags, startTag, endTag)
    parser.setContentHandler(Handler2)
    parser.parse(file2)
    if subdir == "OCL":
        diffRes = diffOCLDirByLine(Handler1, Handler2, str(file1))
    elif subdir == "Template" or subdir == "Template_IMP":
        diffRes = diffTemplateDirByLine(Handler1, Handler2, str(file1))
    else:
        diffRes = diffNormalDirByLine(IDIndex, Handler1, Handler2, str(file1), subdir)
    return diffRes


def diffTemplateDirByLine(Handler1, Handler2, fileName):
    diffRes = []
    fileList1 = Handler1.fileList
    fileList2 = Handler2.fileList
    i, j = 0, 0
    while i < len(fileList1) and j < len(fileList2):
        try:
            i, j, isEnd = diffALineInTemplateDir([0], i, j, fileList1, fileList2, diffRes)
            if isEnd:
                break
        except NoMatchedBlockId:
            printExceptionResult(fileName, fileList1[i], fileList2[j])
            return diffRes
    dealWithRemainedRowsInTemplateDir(i, len(fileList1), fileList1, diffRes, "删除")
    dealWithRemainedRowsInTemplateDir(j, len(fileList2), fileList2, diffRes, "增加")
    return diffRes


# 遍历完两边的文件夹剩下的几行
def dealWithRemainedRowsInTemplateDir(startI, endI, fileList, diffRes, changeType):
    for m in range(startI, endI):
        diffRes.append([changeType, fileList[m][0], ""])


def dealBlockIdDiff(i, j, fileList1, fileList2, IDIndex):
    k = 1
    isEnd = False
    while 1:
        if k >= 40:
            raise NoMatchedBlockId()
        if i == len(fileList1) - 1 or j == len(fileList2) - 1:
            isEnd = True
            break;
        res = skipKLine(IDIndex, fileList1, fileList2, i, j, k);
        if res == "删除":
            i = i + k
            break
        elif res == "增加":
            j = j + k
            break
        k += 1
    return i, j, isEnd


# 对比两个template directory里面的文件
def diffALineInTemplateDir(IDIndex, i, j, fileList1, fileList2, diffRes):
    isEnd = False
    if fileList1[i][0] == fileList2[j][0]:
        # 两个block内容不一样
        if not fileList1[i][1] == fileList2[j][1]:
            deletedAttrs = fileList1[i][1].keys() - fileList2[j][1].keys()
            addedAttrs = fileList2[j][1].keys() - fileList1[i][1].keys()
            intersectAttrs = fileList1[i][1].keys() & fileList2[j][1].keys()
            if deletedAttrs:
                for attr in deletedAttrs:
                    diffRes.append(["修改前有，修改后被删除的attribute", fileList1[i][0], attr])
            if addedAttrs:
                for attr in addedAttrs:
                    diffRes.append(["修改前无，修改后增加的attribute", fileList1[i][0], attr])
            if intersectAttrs:
                for attr in intersectAttrs:
                    if fileList1[i][1][attr] != fileList2[j][1][attr]:
                        diffRes.append(["被修改的attribute", fileList1[i][0], attr])
        i += 1
        j += 1
    # block id 不一样
    else:
        startI = i
        startJ = j
        i, j, isEnd = dealBlockIdDiff(i, j, fileList1, fileList2, IDIndex)
        # 在文档中间被删除或增加的
        dealWithRemainedRowsInTemplateDir(startI, i, fileList1, diffRes, "删除")
        dealWithRemainedRowsInTemplateDir(startJ, j, fileList2, diffRes, "增加")
    return i, j, isEnd


def readfile(filename):
    try:
        filehandle = io.open(filename, 'r', encoding=getEncodingWay(filename))
        text = filehandle.read().splitlines()
        filehandle.close()
        return text
    except IOError as error:
        print('Read file Error:' + str(error))
        return []



def twoFilesIsDifferent(text1_lines, text2_lines):
    for line in difflib.context_diff(text1_lines, text2_lines):
        searchPlus = re.match('\+', line)
        searchMinus = re.match('-', line)
        searchExcMark = re.match('!', line)  # 搜索以感叹号为开头的line
        if searchPlus or searchMinus or searchExcMark:
            return True
    return False


# 返回了一个对比两个xml的html文件
def getDiffHtml(text1_lines, text2_lines, pathName):
    diff2 = difflib.HtmlDiff()  # 创建HtmlDiff 对象
    result = diff2.make_file(text1_lines, text2_lines)  # 通过make_file 方法输出 html 格式的对比结果
    # 将结果写入到result_comparation.html文件中
    try:
        try:
            result_file = open(os.path.join('allResultFiles\\resultXLSX', pathName + '_diff.html'), 'w',
                               encoding="utf-8")
        except:
            result_file = open(os.path.join('allResultFiles\\resultXLSX', pathName + '_diff.html'), 'w', encoding="gbk")
        # result_file.write(codecs.BOM_UTF8)#避免write中文出现乱码
        for line in result:
            result_file.write(line)
        print("=============> Successfully Finished\n")
        result_file.close()
    except IOError as error:
        print('写入html文件错误：{0}'.format(error))


def turnFileIntoHtmlFile(file1, file2, outFileName):
    text1_lines = readfile(file1)
    text2_lines = readfile(file2)
    if twoFilesIsDifferent(text1_lines, text2_lines):
        getDiffHtml(text1_lines, text2_lines, outFileName)


def getEncodingWay(file):
    f = open(file, 'rb')
    data = f.read()
    file_encoding = chardet.detect(data).get('encoding')
    return file_encoding


def tryReadCsv(filename):
    encodings = ['gbk', 'utf-8', 'utf-8-sig', 'GB2312','gb18030', ]
    dataFrame = []
    for e in encodings:
        try:
            dataFrame = pd.read_csv(filename, encoding=e)
            print(e + " can decode "+filename)
            break
        except:
            print("I am trying, but:")
            print(e + " can not decode " + filename)
    return dataFrame


def getListFromCsv(file1, file2):
    try:
        dataframe1 = pd.read_csv(file1, encoding=getEncodingWay(file1))
        dataframe2 = pd.read_csv(file2, encoding=getEncodingWay(file2))
    except:
        dataframe1 = tryReadCsv(file1)
        dataframe2 = tryReadCsv(file2)

    fileList1 = dataframe1.values.tolist()
    fileList2 = dataframe2.values.tolist()
    #print(fileList1)
    return fileList1, fileList2


# 单纯判断 csv文件是否有改变，每一行之间对比是否有差异
def isCSVFileForFileNameSame(file1, file2):
    fileList1, fileList2 = getListFromCsv(file1, file2)
    i, j = 0, 0
    while i < len(fileList1) and j < len(fileList2):
        if fileList1[i] != fileList2[j]:
            return False
        i += 1
        j += 1
    if i != len(fileList1) or j != len(fileList2):
        return False
    return True


# 遍历包含的除了xml外的其他文件夹的差异，譬如ScenList，0_CN_0_SRN_COMM
def iterateOtherDir(path1, path2, columnNames, subdir):
    allDiffRes = []
    allDiffFileNames = []
    for f in os.listdir(path1):
        file1 = os.path.join(path1, f)
        file2 = os.path.join(path2, f)
        if not os.path.exists(file2):
            print(file1 + ' DOES NOT EXIST IN LO_new!')
            continue

        suffix = os.path.splitext(f)[1]
        if suffix == '.csv':
            if subdir == "ScenList":

                diffRes = getDiffScenList(file1, file2, str(f))
                diffRes = diffRes[:len(columnNames)]
                if diffRes:
                    for i in range(len(diffRes)):
                        diffRes[i] = diffRes[i][:len(columnNames) + 1]
                    allDiffRes.append(diffRes)
                    allDiffFileNames.append(f[max(0, len(f) - 30):len(f)])
            elif subdir == "0_CN_0_SRN_COMM":
                diffRes = diff0CNDirByLine([0, 1], file1, file2, str(f))
                if diffRes:
                    for i in range(len(diffRes)):
                        diffRes[i] = diffRes[i][:len(columnNames) + 1]
                    allDiffRes.append(diffRes)
                    allDiffFileNames.append(f[max(0, len(f) - 30):len(f)])
                # print(diffRes)
        elif suffix == '.py' or suffix == '.txt' or suffix == '.xml':
            turnFileIntoHtmlFile(file1, file2, f)
        else:
            print(file1 + " THIS TYPE CAN NOT BE PARSED!")

    if allDiffRes:
        outPath = os.path.join("allResultFiles\\resultXLSX", subdir + ".xlsx")
        print(outPath)
        writeToExcel(allDiffRes, allDiffFileNames, columnNames, outPath, subdir)


# 遍历文件夹中的需要通过contentHandler解析的xml文件并且写入同一个excel表的不同表单内
def iterateXMLFile(path1, path2, allTags, subdir, startTag, endTag, idIndex, contentHandler):
    allDiffRes = []
    allDiffFileNames = []
    for f in os.listdir(path1):
        print(f)
        file1 = os.path.join(path1, f)
        file2 = os.path.join(path2, f)
        if not os.path.exists(file2):
            print(file1 + ' DOES NOT EXIST IN LO_new!')
            continue
        suffix = os.path.splitext(f)[1]
        if suffix == '.xml':
            if subdir == "high_risk_info" and f.startswith("PreciseSceneDefine"):
                turnFileIntoHtmlFile(file1, file2, f)
            else:
                #turnFileIntoHtmlFile(file1, file2, f)
                diffRes = getDiffRes(file1, file2, allTags, startTag, endTag, idIndex, contentHandler, subdir)

                if diffRes:
                    for i in range(len(diffRes)):
                        diffRes[i] = diffRes[i][:len(allTags) + 1]
                        # 改的bug： Integrity和high_risk_info有解析出来是byte的情况
                        for j in range(len(diffRes[i])):
                            try:
                                diffRes[i][j] = str(diffRes[i][j], "utf-8")
                            except:
                                pass
                    allDiffRes.append(diffRes)
                    allDiffFileNames.append(f[max(0, len(f) - 30):len(f)])
        elif suffix == '.py':
            turnFileIntoHtmlFile(file1, file2, f)
        else:
            print(file1 + " THIS TYPE CAN NOT BE PARSED!")
    outPath = os.path.join("allResultFiles\\resultXLSX", subdir + ".xlsx")
    print(outPath)
    if allDiffRes:
        writeToExcel(allDiffRes, allDiffFileNames, allTags, outPath, subdir)


# 对比两个文件夹的文件内容并把内容不同的文件名导出到diffFileNameList
def iterateFileForFileNames(path1, path2, fileNameList, allDirsDiffFileNameList, sheetNames, subdir):
    diffFileNameList = []
    for f in fileNameList:
        file1 = os.path.join(path1, f)
        file2 = os.path.join(path2, f)
        if not os.path.exists(file2):
            print(file1 + ' DOES NOT EXIST IN LO_new!')
            continue
        suffix = os.path.splitext(f)[1]
        if suffix == '.xml' or suffix == '.txt':
            text1_lines = readfile(file1)
            text2_lines = readfile(file2)
            # 判断两个xml文件是否相同
            if twoFilesIsDifferent(text1_lines, text2_lines):
                diffFileNameList.append(f)
        elif suffix == '.csv':
            if not isCSVFileForFileNameSame(file1, file2):
                diffFileNameList.append(f)
    if diffFileNameList:
        sheetNames.append(subdir)
        allDirsDiffFileNameList.append(diffFileNameList)


# 得到某一个文件夹里的 文件夹 和 文件的list
def getDirAndFileInDir(path1, path2):
    dirAndFileInDirList = [[], []]
    for subsubdir in os.listdir(path1):
        if not os.path.exists(path2):
            print(path1 + '\\' + subsubdir + ' DOES NOT EXIST IN LO_new!')
            continue
        if os.path.isdir(subsubdir):
            dirAndFileInDirList[0].append(subsubdir)
        else:
            dirAndFileInDirList[1].append(subsubdir)
    return dirAndFileInDirList


def getDirsOnlyNeedDiffFileNames(allDirsDiffFileNameList, sheetNames, path1, path2, subdir):
    dirAndFileInDirList = getDirAndFileInDir(path1, path2)
    if dirAndFileInDirList[0]:
        for subsubdir in dirAndFileInDirList[0]:
            path1 = os.path.join(path1, subsubdir)
            path2 = os.path.join(path2, subsubdir)
            iterateFileForFileNames(path1, path2, os.listdir(subsubdir), allDirsDiffFileNameList, sheetNames,
                                    subdir + "/" + subsubdir)
    if dirAndFileInDirList[1]:
        iterateFileForFileNames(path1, path2, dirAndFileInDirList[1], allDirsDiffFileNameList, sheetNames, subdir)


def iterateDir(dir1, dir2):
    dir1List = os.listdir(dir1)
    sheetNames = []
    allDirsDiffFileNameList = []
    dirsOnlyNeedDiffFileNames = ["CmeBatchProc", "HwDetectCfg", "LTERebuildTool", "MO_Group",
                                 "MOC_Order", "MPTRebuildTool", "NERebuildTool", "OtherRef", \
                                 "ParameterPolicy", "PoleSiteSelfCfg", "Reference",
                                 "ScriptPackage", "ScriptRightGroup", "SummaryWizard", "SupportInfo", \
                                 "TransOptimize","Parameter Reference", "FeatureManagement",]
    dirsCanBeIgnored = ["BBU_CFG_DATA", "BSDIY", "MODEL", "RF_Res_Power_Spec", "UPG"]
    for subdir in dir1List:
        path1 = os.path.join(dir1, subdir)
        path2 = os.path.join(dir2, subdir)
        print("当前正在遍历的文件夹：")
        print(path1)
        if os.path.isdir(path1):
            # 遍历high_risk_info文件夹
            if subdir in dirsCanBeIgnored:
                continue
            elif subdir == "high_risk_info":
                allTags = ["Type", "MO", "OPType", "ParaId", "ParaValue", "MMLCmd", "CCfmInfo", "ECfmInfo", "Pdt",
                           "ImpactService", "ImpactOM", "OPProperty", "RiskLevel", "PrjGrp"]
                startTag = "HighRiskMML"
                endTag = "PrjGrp"
                idIndex = [0, 1, 4]
                iterateXMLFile(path1, path2, allTags, subdir, startTag, endTag, idIndex, ch1)
            elif subdir in dirsOnlyNeedDiffFileNames:
                getDirsOnlyNeedDiffFileNames(allDirsDiffFileNameList, sheetNames, path1, path2, subdir)
            elif subdir == "ScenList":
                columnName = ["second-level menu", "MOC", "Chinese menu display name"]
                iterateOtherDir(path1, path2, columnName, subdir)
            elif subdir == "Template" or subdir == "Template_IMP":
                allTags = ["className", "attributes"]
                startTag = ""
                endTag = ""
                idIndex = [0]
                iterateXMLFile(path1, path2, allTags, subdir, startTag, endTag, idIndex, ch4)
            elif subdir == "Integrity":
                allTags = ["Id", "MOName", "NewRule", "OldRule", "Pdt", "ErrCode", "CRuleName", "ERuleName",
                           "CRuleDesc",
                           "ERuleDesc", "OclDesc", "NeCode", "OpType", "VerifyData", "Owner", "Comments"]
                startTag = "MO"
                endTag = "Comments"
                idIndex = [0]
                iterateXMLFile(path1, path2, allTags, subdir, startTag, endTag, idIndex, ch1)
            elif subdir == "Assoc_Op":
                allTags = ["rule_no", "parent_object", "op_type", "child_object", "range", "field", "matrix",
                           "condition", "item",
                           "notes", "desc", "analysis"]
                startTag = "rule"
                endTag = "analysis"
                idIndex = [0]
                iterateXMLFile(path1, path2, allTags, subdir, startTag, endTag, idIndex, ch2)
            elif subdir == "OCL":
                allTags = ["ParaId", "MOName", "Type", "ParaName", "NewRule", "OldRule", "Pdt", "ErrCode", "RuleName", \
                           "RuleContent", "ERuleContent", "OCLDesc", "NeCode", "OpType", "VerifyData", "Owner",
                           "Comments"]
                startTag = ""
                endTag = "Comments"
                idIndex = [0]
                iterateXMLFile(path1, path2, allTags, subdir, startTag, endTag, idIndex, ch3)
            elif subdir == "0_CN_0_SRN_COMM":
                columnName = ["Classification", "MOC", "LIST", "Cabinet No.", "Subrack No.",
                              "Responsibility Project Team", "Remark", "Check results", "Slot No.", "Asso Board"]
                iterateOtherDir(path1, path2, columnName, subdir)
            elif subdir == "ExtensionCenter":
                iterateOtherDir(path1, path2, [], subdir)
            # 把只需要diffFileName的所有的directory当作sheetname，每个sheet里面文件夹里所有改变了的文件的名字
            
            else:
                print(subdir + " have not be parsed!")
            # 文件夹里面只有.py或者.txt文件，直接输出html对比文件
    # for循环结束后把所有diff file写入
    writeDiffFileNameIntoExcel(allDirsDiffFileNameList, sheetNames)


def iterateAllFilesIntoHtml(dir1, dir2):
    dirsCanBeIgnored = ["BBU_CFG_DATA", "BSDIY", "MODEL", "RF_Res_Power_Spec", "UPG"]
    for subdir in dir1:
        path1 = os.path.join(dir1, subdir)
        path2 = os.path.join(dir2, subdir)
        if subdir in dirsCanBeIgnored:
            for file in subdir:
                file1 = os.path.join(path1, file)
                file2 = os.path.join(path2, file)
                if not os.path.exists(file2):
                    print(file2 + ' DOES NOT EXIST IN LO_new!')
                    continue
                turnFileIntoHtmlFile(file1, file2, file)


def writeDiffFileNameIntoExcel(allDirsDiffFileNameList, diffFileNameList):
    dataframes = []
    for diffRes in allDirsDiffFileNameList:
        dataframe = pd.DataFrame(diffRes, columns=["Diff File Name"])
        dataframes.append(dataframe)
    i = 0
    outPath = os.path.join("allResultFiles", "diffFileNames.xlsx")
    with pd.ExcelWriter(outPath) as writer:
        for dataframe in dataframes:
            try:
                dataframe.to_excel(writer, sheet_name=diffFileNameList[i])
                i += 1
            except:
                print("ERROR writing to diffFileNames.xlsx")


def getDiffResRow(originList, changeType, diffRes, n):
    row = copy.deepcopy(originList[1][n])
    row.insert(0, originList[0])
    row.insert(0, changeType)
    diffRes.append(row)


# 比较一个block里面的三四列的异同
def getThreeFourColsDiff(list1, list2, i, j, diffRes):
    m = 0
    block1RowNum = len(list1[i][1])
    block2RowNum = len(list2[j][1])
    while m < block1RowNum:
        if m >= block2RowNum:
            for n in range(m, block1RowNum):
                getDiffResRow(list1[i], "修改前", diffRes, n)
                diffRes.append(["修改后", list2[j][0], '', ''])
            break
        if list1[i][1][m] != list2[j][1][m]:
            getDiffResRow(list1[i], "修改前", diffRes, m)
            getDiffResRow(list2[j], "修改后", diffRes, m)
        m += 1

    if block2RowNum > block1RowNum:
        for n in range(m, block2RowNum):
            diffRes.append(["修改前", list1[i][0], '', ''])
            getDiffResRow(list2[j], "修改后", diffRes, n)


# 比较excel里第二列是否一致
def diffALineInExcel(i, j, list1, list2, diffRes):
    # 同样的block ID
    isEnd = False
    if list1[i][0] == list2[j][0]:
        # 两个block内容不一样
        getThreeFourColsDiff(list1, list2, i, j, diffRes)
        i += 1
        j += 1
    # block id 不一样
    else:
        startI = i
        startJ = j
        i, j, isEnd = dealBlockIdDiff(i, j, list1, list2, [])
        for m in range(startI, i):
            row1 = ["删除", list1[m][0], "", ""]
            diffRes.append(row1)
        for m in range(startJ, j):
            row1 = ["增加", list2[m][0], "", ""]
            diffRes.append(row1)
    # print(diffRes)
    return i, j, isEnd


# 处理ScenList得到的list，删掉只有第一列的那一行，将剩下的按照block放进新列表里
def getNewList(oldList):
    newList = []
    threeFourCols = []
    index = ""
    for i in range(len(oldList)):
        if not pd.isnull(oldList[i][0]) and pd.isnull(oldList[i][1]):
            continue
        # 第二列不为null，就是一个block的开始
        if not pd.isnull(oldList[i][1]):
            if threeFourCols:
                newList.append([index, threeFourCols])
            threeFourCols = []
            index = oldList[i][1]
        threeFourCols.append([oldList[i][2], oldList[i][3]])
    return newList


def getDiffScenList(file1, file2, fileName):
    try:
        list1, list2 = getListFromCsv(file1, file2)
    except:
        return []
    diffRes = []
    list1 = getNewList(list1)
    list2 = getNewList(list2)
    file1BlockNum = len(list1)
    file2BlockNum = len(list2)
    i, j = 0, 0
    while i < file1BlockNum and j < file2BlockNum:
        try:
            i, j, isEnd = diffALineInExcel(i, j, list1, list2, diffRes)
            if isEnd:
                break
        except NoMatchedBlockId:
            printExceptionResult(fileName, list1[i], list2[j])
            return diffRes
    dealWithRemainedRows(i, len(list1), list1, diffRes, "删除")
    dealWithRemainedRows(j, len(list2), list2, diffRes, "增加")
    return diffRes


def main():
    dir1 = os.path.join(os.getcwd(), "LO_old")
    dir2 = os.path.join(os.getcwd(), "LO_new")
    if not os.path.exists(os.path.join(os.getcwd(), "allResultFiles")):
        os.makedirs(os.getcwd()+"\\allResultFiles")
    if not os.path.exists(os.getcwd()+"\\allResultFiles\\resultXLSX"):
        os.makedirs(os.getcwd()+"\\allResultFiles\\resultXLSX")
    iterateDir(dir1, dir2)
'''


def main():
    path1 = "LO_old/MO_Group"
    path2 = "LO_new/MO_Group"
    allDirsDiffFileNameList = []
    sheetNames = []
    getDirsOnlyNeedDiffFileNames(allDirsDiffFileNameList, sheetNames, path1, path2, "Parameter Reference")
'''

if __name__ == "__main__":
    main()






'''
def getThreeFourColsDiff(list1, list2, i, j, diffRes):
    m, n = 0, 0
    block1RowNum = len(list1[i][1])
    block2RowNum = len(list2[j][1])
    print(list1[i][1])
    print(list2[j][1])

    while m < block1RowNum and n < block2RowNum:
        print()
        #第三列的 内容 一样
        if (list1[i][1][m][0] == list2[j][1][n][0]) or (pd.isnull(list1[i][1][m][0]) and pd.isnull(list2[j][1][n][0])):
            # 两个block内容一样
            if (list1[i][1][m][1] == list2[j][1][n][1]) or (pd.isnull(list1[i][1][m][1]) and pd.isnull(list2[j][1][n][1])):
                continue
            else:
                row1 = copy.deepcopy(list1[i][1][m])
                row1.insert(0, list1[i][0])
                row1.insert(0, "修改前")
                diffRes.append(row1)
                row2 = copy.deepcopy(list2[j][1][n])
                row2.insert(0, list2[j][0])
                row2.insert(0, "修改后")
                diffRes.append(row2)
            m += 1
            n += 1
        #第三列的 内容 不一样
        else:                                                             
            k = 1                                                         
            startI = m
            startJ = n
            while 1:                                                      
                res = skipKLineInExcel(list1[i][1], list2[j][1], m, n, k);
                print(res)
                if res == "删除":                                           
                    m = m + k
                    break                                                 
                elif res == "增加":                                         
                    n = n + k
                    break                                                 
                k += 1                                                    
            for t in range(startI, i):
                row1 = ["删除", list1[i][0], list1[i][1][t][0], list1[i][1][t][1]]
                diffRes.append(row1)                                      
            for t in range(startJ, j):
                row1 = ["增加", list2[j][0], list2[j][1][t][0], list2[j][1][t][1]]
                diffRes.append(row1)                                                                 
    dealWithRemainedRows(m, list1[i][1], diffRes, "删除")
    dealWithRemainedRows(n, list2[j][1], diffRes, "增加")


'''