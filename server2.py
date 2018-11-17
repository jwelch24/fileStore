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

PORT_NUMBER = 80



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

    directory = {}
    directory["develop"] = {"serverObjectType":"directory"}
    directory["feature"] = {"serverObjectType":"directory"}
    directory["release"] = {"serverObjectType":"directory"}
    directory["release"]["1.1.0"] = {"serverObjectType":"directory"}
    directory["release"]["1.2.0"] = {"serverObjectType":"directory"}
    directory["release"]["1.3.0"] = {"serverObjectType":"directory"}
    directory["feature"]["SOF-1234-my-first-feature"] = {"serverObjectType":"directory"}
    directory["feature"]["SOF-5678-my-second-feature"] = {"serverObjectType":"directory"}

    myhash = ''.join(random.choice(string.hexdigits.lower()) for _ in range(7))
    for i in range(0,30):

        if random.random() > 0.8:
            myhash = ''.join(random.choice(string.hexdigits.lower()) for _ in range(7))

        for file_type in ["cx1","rx1","cx2","mx1"]:
            for variant in ["","-dev"]:
                for signed in ["",".signed",".dev-signed"]:
                    file_name = file_type + "-" + myhash + variant + ".img" + signed
                   # print file_name
                    fobj = CreateObject(file_name,upload_time=time.time()+i*86400,parent_dir=["develop"],metadata={'type':file_type,'component':'zap'})
                    file_id = fobj["saveFile"]
                    files[file_id] = copy.deepcopy(fobj)

                    directory["develop"][file_id] = {}

    for feature in directory["feature"]:
        if feature != "serverObjectType":
            myhash = ''.join(random.choice(string.hexdigits.lower()) for _ in range(7))
            for i in range(0,10):
                
                for file_type in ["cx1","rx1","cx2","mx1"]:
                    for variant in ["","-dev"]:
                        for signed in ["",".signed",".dev-signed"]:
                            file_name = file_type + "-" + myhash + variant + ".img" + signed
                            fobj = CreateObject(file_name,upload_time=time.time()+i*86400,parent_dir=["feature",feature],metadata={'type':file_type,'component':'zap'})
                            file_id = fobj["saveFile"]
                            files[file_id] = copy.deepcopy(fobj)
                            directory["feature"][feature][file_id] = {}

    for release in directory["release"]:
        if release != "serverObjectType":
            myhash = ''.join(random.choice(string.hexdigits.lower()) for _ in range(7))
            for i in range(0,1):
                
                for file_type in ["cx1","rx1","cx2","mx1"]:
                    for variant in ["","-dev"]:
                        for signed in ["",".signed",".dev-signed"]:
                            file_name = file_type + "-" + myhash + variant + ".img" + signed
                            fobj = CreateObject(file_name,upload_time=time.time()+i*86400,parent_dir=["release",release],metadata={'type':file_type,'component':'zap'})
                            file_id = fobj["saveFile"]
                            files[file_id] = copy.deepcopy(fobj)
                            directory["release"][release][file_id] = {}

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

        return rh.sendResponse(200,json.dumps(filtered_list[0:100]),headers=[('Access-Control-Allow-Origin','*'),('Content-type','application/json')]) 

        msg = "<h1>Generic Archive Server</h1><hr>"
        end_time = time.time()
        msg += "Found: "+str(len(filtered_list))+" files in "+str(end_time-start_time)[0:5]+" seconds. Showing "+str(start)+" to "+str(end)+".<hr>"
        for file in filtered_list[start:end]:
            msg += formatFileInfo(file)

        return rh.sendResponse(200,msg,headers=(('Content-type','text/html'))) 



        # files = []
        # for f in myHandler.files:
        #     files.append(myHandler.files[f])
        # return rh.sendResponse(200,json.dumps(files),headers=[('Access-Control-Allow-Origin','*'),('Content-type','application/json')]) 


    def apiNumFiles(rh):
        return rh.sendResponse(200,len(myHandler.files),headers=[('Access-Control-Allow-Origin','*'),('Content-type','application/json')]) 


    def apiListDir(rh):

        info = {}
        info["child_dirs"] = {}
        info["child_files"] = {}
        return rh.sendResponse(200,len(myHandler.files),headers=[('Access-Control-Allow-Origin','*'),('Content-type','application/json')]) 


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
        directory = self.path.split("/")[1:-1]

        count = 0
        # boundary = ""
        # for line in self.rfile:
        #     if count == 0:
        #         boundary = line

            #if "Content-Disposition" in line:
            #    print line.split(";")
             # do something with the line
            #if boundary in line:
            #    print "boundary"

        current_level = myHandler.directory
        for d in directory:
            if d not in current_level:
                current_level[d] = {"serverObjectType":"directory"}

            current_level = current_level[d]

        fobj = CreateObject(file_name,parent_dir=directory,metadata={'type':'unknown'})
        file_id = fobj["saveFile"]

        # calculate MD5
        # calculate SHA256
        myHandler.files[file_id] = copy.deepcopy(fobj)

        current_level[file_id] = {}

        return self.sendResponse(200,file_id+"\n",headers=[('Access-Control-Allow-Origin','*'),('Content-type','application/json')])

    def do_DELETE(self):
        file_id = self.path.split("/")[-1]

        if file_id not in myHandler.files:
            return self.sendResponse(404)

        parent_dir = myHandler.files[file_id]["parentDir"].split("/")

        directory = myHandler.directory
        for path in parent_dir:
            directory = directory[path]

        if file_id not in directory:
            return self.sendResponse(500)

        del directory[file_id]
        del myHandler.files[file_id]

        return self.sendResponse(200)

try:
    #Create a web server and define the handler to manage the #incoming request
    server = HTTPServer(('', PORT_NUMBER), myHandler)
    print 'Started httpserver on port ' , PORT_NUMBER
    
    #Wait forever for incoming htto requests
    server.serve_forever()

except KeyboardInterrupt:
    print '^C received, shutting down the web server'
    server.socket.close()