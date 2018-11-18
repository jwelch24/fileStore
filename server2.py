#!/usr/bin/python
import json
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
import time
import copy
import random
import fnmatch
import datetime
import string
import uuid
import os
import shutil
import hashlib

PORT_NUMBER = 80
BUF_SIZE = 65536  # lets read stuff in 64kb chunks!
DEBUG = True

def fileHashes(file):
    md5 = hashlib.md5()
    sha256 = hashlib.sha256()

    with open(file, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            md5.update(data)
            sha256.update(data)

    return md5.hexdigest() , sha256.hexdigest()

def CreateObject(filename,upload_time=None,parent_dir=None,metadata={}):
    new_object = {}
    new_object["filename"] = filename
    
    new_object["md5sum"] = ''.join(random.choice(string.hexdigits.lower()) for _ in range(32))
    new_object["sha256"] = ''.join(random.choice(string.hexdigits.lower()) for _ in range(64))

    if upload_time:
        new_object["uploadedAt"] = upload_time
    else:
        new_object["uploadedAt"] = time.time()

    new_object["uploadDate"] = datetime.datetime.utcfromtimestamp(new_object["uploadedAt"]).strftime("%Y-%m-%d")
    new_object["uploadTime"] = datetime.datetime.utcfromtimestamp(new_object["uploadedAt"]).strftime("%H:%M")
    new_object["serverObjectType"] = "file"
    new_object["size"] = int(100000000*random.random())
    new_object["saveFile"] = str(uuid.uuid4())

    new_object["parentDir"] = ""
    if parent_dir:
        for part in parent_dir:
            new_object["parentDir"] += part + "/"

        new_object["parentDir"] = new_object["parentDir"][:-1]

    new_object["metadata"] = copy.deepcopy(metadata)
    new_object["key"] = new_object["saveFile"]

    return copy.deepcopy(new_object)

def formatFileInfo(file):

    msg = ""
    msg += '<div style="background-color:#eee;padding:10px;border-radius:10px;font-family:arial">'
    msg += '<span style="width:200px"><strong>'+file['filename']+"</strong></span> <hr>"
    msg += "uploadDate: "+file['uploadDate'] + "<br>"
    msg += "uploadDate: "+file['uploadDate'] + "<br>"
    msg += "uploadTime: "+file['uploadTime'] + "<br>"
    msg += "size: "+str(int(float(file['size'])/1048576)) + "MB<br>"
    msg += "md5sum: "+str(file['md5sum']) + "<br>"
    msg += "sha256: "+str(file['sha256']) + "<br>"
    msg += "saveFile: "+str(file['saveFile']) + "<br><br>"
    msg += "<b>metadata</b><br>"
    for field in file['metadata']:
        msg += field+": " + str(file['metadata'][field]) + "<br>"
    msg += '<hr><a href="'+  "/download?saveFile=" + file["saveFile"]  + '">'+ 'Download' + '</a><hr>'
    msg += '</div><br>'  

    return msg

def matchQuery(query,f):
    for q in query:
        q_levels = q[0].split(".")
        file_data = copy.deepcopy(f)
        for r in q_levels:
            file_data = file_data[r]

        file_match = False
        for specified_matches in q[1].split(","):
            if fnmatch.fnmatch(str(file_data),specified_matches):
                file_match = True

        if not file_match:
            break

    return file_match

def findLatestFile(files):

    if len(files) == 0:
        return []

    latestFile = files[0]
    for f in files:
        if f["uploadedAt"] > latestFile["uploadedAt"]:
            latestFile = f

    files = []
    files.append(latestFile)

    return latestFile

#This class will handles any incoming request from
#the browser 
class myHandler(BaseHTTPRequestHandler):
    
    def sendResponse(self,code,msg=None,headers=None):
        self.send_response(code)
        if headers:
            for h in headers:
                print h
                self.send_header(h[0],h[1])

        if DEBUG:
            # ('Access-Control-Allow-Origin','*')
            print "Adding debug headers"
            self.send_header('Access-Control-Allow-Origin','*')
#        self.send_header('Content-type','text/html')
        self.end_headers()
        if msg:
            self.wfile.write(msg)

    def upOne(self):

        up_one = ""
        for part in self.path.split("/")[:-1]:
            up_one += part + "/"
        up_one = up_one[:-1]

        if len(up_one) == 0:
            up_one = "/"

        return up_one

    def splitQuery(self):
        query = None
        query_parameters = []
        findLatest = False
        sortBy = None
        page = None
        if len(self.path.split("?")) == 2:
            query =  self.path.split("?")[1]
            
            for q in query.split("&"):
                # Look for special cases
                key = q.split("=")[0]
                value = q.split("=")[1].replace("%","?")

                if key == "uploadDate":
                    if value == "latest":
                        findLatest = True
                    else:
                        query_parameters.append((key,value))

                elif key == "sortBy":
                    if sortBy:
                        return self.sendResponse(400,"Cannot have more than one sortBy query")
                    sortBy = value

                elif key == "page":
                    page = int(value)

                else:
                    query_parameters.append((key,value))



            query = query_parameters

        return query , findLatest , sortBy , page

    files = {}

    if os.path.isfile("files.json"):
        with open("files.json") as file: # Use file to refer to the file object

            files = json.loads(file.read())

    else:
        with open('files.json', 'w') as file:  # Use file to refer to the file object

            file.write(json.dumps(files))

    directory = {}


    def listFiles(rh):
        try:
            query , findLatest , sortBy , page = rh.splitQuery()
        except:
            return rh.sendResponse(400)

        start_time = time.time()
        #if query:
        filtered_list = []
        for f in myHandler.files:
            if query:
                if matchQuery(query,myHandler.files[f]):
                    filtered_list.append(myHandler.files[f])
            else:
                filtered_list.append(myHandler.files[f])

        if findLatest:
            filtered_list = findLatestFile(filtered_list)

        start = 0 
        end = 100
        if page:
            page_size = 100
            start = (page-1)*page_size
            if start > len(filtered_list):
                return rh.sendResponse(404,"No page found")
            end = page*page_size
            if end > len(filtered_list):
                end = len(filtered_list)

        msg = "<h1>Generic Archive Server</h1><hr>"
        end_time = time.time()
        msg += "Found: "+str(len(filtered_list))+" files in "+str(end_time-start_time)[0:5]+" seconds. Showing "+str(start)+" to "+str(end)+".<hr>"
        for file in filtered_list[start:end]:
            msg += formatFileInfo(file)

        return rh.sendResponse(200,msg,headers=(('Content-type','text/html'))) 

            #return rh.sendResponse(200,json.dumps(filtered_list, sort_keys=True, indent=4, separators=(',', ': ')))    

        #else:
        #    return rh.sendResponse(200,json.dumps(myHandler.files, sort_keys=True, indent=4, separators=(',', ': ')))  

    def downloadFile(rh):
        return rh.sendResponse(200,"Download File")

    def numFiles(rh):
        tot_size = 0
        for f in myHandler.files:
            tot_size += int(myHandler.files[f]["size"]) / 1048576
        #return rh.sendResponse(200,str(len(myHandler.files))+" taking up "+str(tot_size)+"MB")
        return rh.sendResponse(200,str(len(myHandler.files))+" taking up "+str(tot_size)+"MB",headers=[('Access-Control-Allow-Origin','*'),('Content-type','text/html')])

    def rootDir(rh):
        msg = "<h1>Generic Archive Server</h1><hr>"
        msg += '<a href="' + rh.path +"directory"  + '"">'+ "Directory List" + '</a><br>'
        msg += '<a href="' + rh.path +"files"  + '"">'+ "File List" + '</a><br>'
        return rh.sendResponse(200,msg,headers=(('Content-type','text/html'))) 



    def apiFiles(rh):
        try:
            query , findLatest , sortBy , page = rh.splitQuery()
        except:
            return rh.sendResponse(400)

        start_time = time.time()
        #if query:
        filtered_list = []
        for f in myHandler.files:
            if query:
                if matchQuery(query,myHandler.files[f]):
                    filtered_list.append(myHandler.files[f])
            else:
                filtered_list.append(myHandler.files[f])

        if findLatest:

            latest_file = findLatestFile(filtered_list)
            filtered_list = [latest_file]

        start = 0 
        end = 100
        if page:
            page_size = 100
            start = (page-1)*page_size
            if start > len(filtered_list):
                return rh.sendResponse(404,"No page found")
            end = page*page_size
            if end > len(filtered_list):
                end = len(filtered_list)

        print len(filtered_list)

        if len(filtered_list) == 0:
            return rh.sendResponse(404,json.dumps(filtered_list),headers=[('Content-type','application/json')]) 

        print json.dumps(filtered_list)

        # Return the list of files sorted by time uploaded (newest first)
        sorted_list = sorted(filtered_list, key=lambda k: time.time() - k['uploadedAt']) 
        return rh.sendResponse(200,json.dumps(sorted_list),headers=[('Content-type','application/json')]) 

        msg = "<h1>Generic Archive Server</h1><hr>"
        end_time = time.time()
        msg += "Found: "+str(len(filtered_list))+" files in "+str(end_time-start_time)[0:5]+" seconds. Showing "+str(start)+" to "+str(end)+".<hr>"
        for file in filtered_list[start:end]:
            msg += formatFileInfo(file)

        return rh.sendResponse(200,msg,headers=(('Content-type','text/html'))) 



        # files = []
        # for f in myHandler.files:
        #     files.append(myHandler.files[f])
        # return rh.sendResponse(200,json.dumps(files),headers=[('Content-type','application/json')]) 


    def apiNumFiles(rh):
        return rh.sendResponse(200,len(myHandler.files),headers=[('Content-type','application/json')]) 


    def apiListDir(rh):

        info = {}
        info["child_dirs"] = {}
        info["child_files"] = {}
        return rh.sendResponse(200,len(myHandler.files),headers=[('Content-type','application/json')]) 


    routes = {}
    routes["GET"]={}
    routes["GET"]["/"] = rootDir
    routes["GET"]["/api/files"]  = apiFiles
    routes["GET"]["/api/numfiles"]  = apiNumFiles
    routes["GET"]["/api/directory"]  = apiListDir
    routes["GET"]["/files"]  = listFiles
    routes["GET"]["/download"]  = downloadFile
    routes["GET"]["/numfiles"]  = numFiles

    #Handler for the GET requests
    def do_GET(self):
        start_time = time.time()

        if "/" == self.path:
            print "Getting root for static content"
            return self.sendResponse(200)

        if "/api/files" == self.path[0:10]:
            return myHandler.routes["GET"]["/api/files"](self)

        if "/api/numfiles" == self.path[0:13]:
            return myHandler.routes["GET"]["/api/numfiles"](self)

        if "/api/directory" == self.path[0:14]:
            return myHandler.routes["GET"]["/api/directory"](self)

        if "/" == self.path[0] and len(self.path) == 1:
            return myHandler.routes["GET"]["/"](self)

        if "/files" == self.path[0:6]:
            return myHandler.routes["GET"]["/files"](self)

        if "/download" == self.path[0:9]:
            return myHandler.routes["GET"]["/download"](self)

        if "/numfiles" == self.path[0:9]:
            return myHandler.routes["GET"]["/numfiles"](self)

        query , findLatest , sortBy , page = self.splitQuery()

        uri = self.path.split("?")[0]
        split_path = uri.split("/")[1:]
        split_path[0] = "/" + split_path[0]
        split_path[-1] = split_path[-1].replace("%","?")

        if self.path[0:10] == "/directory" or self.path[0:9] == "/download":
            
            download_file = True if self.path[0:9] == "/download" else False
            
            split_path = split_path[1:]
            current_level = myHandler.directory
            for path in split_path:
                if path in current_level:
                    current_level = current_level[path]
                else:
                    files_found = []
                    for entry in current_level:
                        if entry in myHandler.files:
                            if fnmatch.fnmatch(myHandler.files[entry]["filename"], path):#path == myHandler.files[entry]["filename"]:
                                files_found.append(copy.deepcopy(myHandler.files[entry]))

                    # If a set of query parameters has been specified then filter the list
                    if query:
                        filtered_list = []

                        for f in files_found:
                            if matchQuery(query,f):
                                filtered_list.append(f)

                        files_found = filtered_list

                    if findLatest:
                        latestFile = files_found[0]
                        for f in files_found:
                            if f["uploadedAt"] > latestFile["uploadedAt"]:
                                latestFile = f

                        files_found = []
                        files_found.append(latestFile)

                    msg = "<h1>Generic Archive Server</h1><hr>"
                    up_dir = self.upOne()
                    if up_dir != "/":
                        msg = '<h1>Generic Archive Server</h1><br><a href="'+ self.upOne()  + '">'+ 'back' + '</a><hr>'

                    end_time = time.time()
                    msg += "Found: "+str(len(files_found))+" files in "+str(end_time-start_time)[0:5]+" seconds<hr>"

                    for file in files_found[0:100]:
                        msg += formatFileInfo(file)

                    if len(files_found) == 1 and download_file:
                        return self.sendResponse(200,"Downloading: "+files_found[0]["saveFile"])
                    else:
                        print 1
                        return self.sendResponse(200,msg,headers=(('Content-type','text/html')))  

            child_dirs = []
            child_files = []
            found_child_dir = False
            for obj in current_level:
                if "serverObjectType" in current_level[obj]:
                    child_dirs.append(obj)
                    found_child_dir = True
                else:
                    if obj != "serverObjectType":
                        child_files.append(myHandler.files[obj])

            if found_child_dir:

                current_level = child_dirs
                msg = "<h1>Generic Archive Server</h1><hr>"

                up_dir = self.upOne()
                if up_dir != "/":
                    msg = '<h1>Generic Archive Server</h1><br><a href="'+ self.upOne()  + '">'+ 'back' + '</a><hr>'

                for folder in current_level:
                    msg += '<a href="' + self.path +"/"+ folder  + '"">'+ folder + '</a><br>'

                msg += "<hr>"
                for file in child_files[0:100]:
                    msg += formatFileInfo(file)

                return self.sendResponse(200,msg,headers=(('Content-type','text/html')))       

            else:
                all_files = []
                for obj in current_level:
                    if obj != "serverObjectType":
                        all_files.append(myHandler.files[obj])

                current_level = all_files

            if query:
                filtered_list = []

                for f in current_level:
                    if matchQuery(query,f):
                        filtered_list.append(f)

                current_level = filtered_list

            msg = "<h1>Generic Archive Server</h1><hr>"

            up_dir = self.upOne()
            if up_dir != "/":
                msg = '<html><h1>Generic Archive Server</h1><br><a href="'+ self.upOne()  + '">'+ 'back' + '</a><hr>'
                end_time = time.time()
                msg += "Found: "+str(len(current_level))+" files in "+str(end_time-start_time)[0:5]+" seconds<hr>"

            for file in current_level:
                msg += formatFileInfo(file) 

            msg += "</html>"
            return self.sendResponse(200,msg,headers=(('Content-type','text/html')))  

            #return self.sendResponse(200,json.dumps(current_level, sort_keys=True, indent=4, separators=(',', ': ')))
     
    def do_PATCH(self):
        file_id = self.path.split("/")[-1]

        if file_id not in myHandler.files:
            return self.sendResponse(404)

        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)

        new_data = json.loads(body)
        for field in new_data:
            if field in ["md5","size","saveFile"]:
                print "Cannot update these values"

            if field == "parentDir":
                print "Moving file from " + myHandler.files["parentDir"] + " to " + new_data[field]

            myHandler.files[file_id][field] = new_data[field]

        return self.sendResponse(205)

    def do_POST(self):

        file_name = self.path.split("/")[-1]
        directory = self.path.split("/")[1:]

        count = 0
        boundary = ""
        content = ""
        skip = False
        tempFile = str(uuid.uuid4())
        f = open(tempFile, "w")
        count = 0


        totalLength = self.headers['Content-Length']
        ctype = self.headers['Content-Type']

        if "boundary=" in ctype:            
            boundary = ctype.split("boundary=")[1].split("-")[-1]

        bytesRemaining = int(totalLength)
        boundaryLength = 0
        written = False
        self.sendResponse(100)
        fileName = ""
        for line in self.rfile:
            count += 1
            bytesRemaining -= len(line)

            if boundary in line:
                boundaryLength = len(line)

            if skip:
                skip = False
                continue

            if "WebKitFormBoundary" in line:
                boundary = line
                boundaryLength = len(line)
                continue

            if "Content-Disposition" in line:
                if "filename=" in line:
                    fileName = line.split("filename=")[-1]
                continue
            if "Content-Type" in line:
                skip = True
                continue

            if boundary in line:

                if bytesRemaining > 0:
                    if bytesRemaining == len(boundary) + 2:
                        break
                else:
                    break
            else:

                if bytesRemaining == boundaryLength+2:
                    f.write(line[:-2]) 
                    break
                else:
                    f.write(line)

        current_level = myHandler.directory
        for d in directory:
            if d not in current_level:
                current_level[d] = {"serverObjectType":"directory"}

            current_level = current_level[d]

        
        fileName = fileName.split('"')[1]

        fobj = CreateObject(fileName,parent_dir=directory,metadata={'type':'unknown'})
        file_id = fobj["saveFile"]
        fobj["size"] = os.path.getsize(tempFile)
        fobj["md5sum"] , fobj["sha256"] = fileHashes(tempFile)

        shutil.move(tempFile,"files/{}".format(fobj["saveFile"]))
        myHandler.files[file_id] = copy.deepcopy(fobj)

        current_level[file_id] = {}
        # Update the file
        with open('files.json', 'w') as file:  
            file.write(json.dumps(myHandler.files))

        return self.sendResponse(200,file_id+"\n",headers=[('Content-type','application/json')])

    def do_OPTIONS(self):
        return self.sendResponse(200,headers=[("Access-Control-Allow-Methods","GET, POST, OPTIONS, PUT, DELETE"),
                                              ('Content-type','application/json')])

    def do_DELETE(self):
        print "deleteing file"
        file_id = self.path.split("/")[-1]

        if file_id not in myHandler.files:
            return self.sendResponse(404,headers=[('Content-type','application/json')])

        parent_dir = myHandler.files[file_id]["parentDir"].split("/")

        directory = myHandler.directory
        for path in parent_dir:
            directory = directory[path]

        if file_id not in directory:
            return self.sendResponse(500,headers=[('Content-type','application/json')])

        del directory[file_id]
        del myHandler.files[file_id]

        return self.sendResponse(200,headers=[('Content-type','application/json')])

try:
    #Create a web server and define the handler to manage the #incoming request
    server = HTTPServer(('', PORT_NUMBER), myHandler)
    print 'Started httpserver on port ' , PORT_NUMBER
    
    #Wait forever for incoming htto requests
    server.serve_forever()

except KeyboardInterrupt:
    print '^C received, shutting down the web server'
    server.socket.close()