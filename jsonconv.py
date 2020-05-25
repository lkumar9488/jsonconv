#!/usr/bin/env python2.7
import sys
import os

import json
import ast
import re
import subprocess

# Helper functions to convert a Json String payload to Dictionary
# Also converts map style lists to actual lists


class Convertor(object):
    def __init__(self, logging=False):
        self.logging = logging

    def debugprint(self, *args):
        if self.logging:
            for a in args:
                print(a)
            print("\n")

    def __format_convert(self, val):
        try:
            return ast.literal_eval(val)
        except:
            # Python boolean evaluation is case sensitive, hence convert true/false appropriately
            if val == "true":
                return True
            elif val == "false":
    	        return False
            return val
            
    def __uppercase_for_dict_keys(self,lower_dict):
        upper_dict = {}
        for k, v in lower_dict.items():
            if isinstance(v, dict):
                v = self.__uppercase_for_dict_keys(v)
            if k != "table-index":    
                s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', k)
                upper_dict[re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).upper()] = v
        return upper_dict    
       
    # __parse calls this when app_data is of type dictionary.
    # this function is invoked recursively
    def __parse_helper_dictionary(self, app_data, k, v):
        global param_no_format_conv
        self.debugprint("key", k)
        if isinstance(v, dict):
            self.debugprint(k, "is dictionary")
            if self.__is_list(v):
                self.debugprint(k, "to be converted to list")
                klist = v.keys()
                klist.sort()
                list_data = []
                for listk in klist:
                    list_data.append(v[listk])
                self.debugprint("sorted list",list_data)
                app_data[k] = self.__parse(list_data)
            else:
                app_data[k] = self.__parse(v)
        else:
            if (param_no_format_conv != "none") and (k in param_no_format_conv):
                app_data[k] = v
            else:
                app_data[k] = self.__format_convert(v)
        return app_data

    # __parse calls this when app_data is of type list.
    # this function is invoked recursively
    def __parse_helper_list(self, app_data, v):
        if isinstance(v, dict):
            self.debugprint("from list value is dictionary")
            if self.__is_list(v):
                self.debugprint("value to be converted to list")
                klist = v.keys()
                klist.sort()
                list_data = []
                for listk in klist:
                    list_data.append(v[listk])
                self.debugprint("sorted list",list_data)
                app_data.append(self.__parse(list_data))
            else:
                app_data.append(self.__parse(v))
        return app_data

    def __parse(self, data):
        if isinstance(data, dict):
            app_data = {}
            for k, v in data.items():
                app_data = self.__parse_helper_dictionary(app_data, k, v)
            return app_data
        else:
            app_data = []
            for v in data:
                app_data = self.__parse_helper_list(app_data, v)
            processed_list = self.post_process(app_data)
            return processed_list

    def __is_list(self, data):
        klist = data.keys()
        try:
            klist = map(int, klist)
        except ValueError:
            return False
        klist.sort()
        list_len = len(klist)
        try:
            first = int(klist[0])
            last = int(klist[list_len-1])
            if first == 0 and last == (list_len-1):
                return True
            else:
                return False
        except ValueError:
            return False

    def convert_conf(self, cfg_data):
        global module_name
        json_data = json.loads(cfg_data)
        converted_data = self.__parse(json_data)
        return converted_data

    def post_process(self, json_list_data):
        op_list = []
        for item in json_list_data:
            if isinstance(item, dict):
                try:
                    del item["table-index"]
                except:
                    pass
            op_list.append(item)
        return op_list

class CfgWriter(object):

    def write_file(self, filename, data):
        fwp = open(filename, "w")
        fwp.write(json.dumps(data))
        fwp.close()

    """
    Writes Values of level 1 keys to files with level_1 key as name, returns a map with names of files written
    eg
    {
        "level_1_k1" :
        {
            //level2 content
        },
        "level_1_k2":{
            //level2 content

        }
    }
    writes files level_1_k1.conf and level_1_k2.conf
    prints to stdout:
    {
        "level_1_k1": "conf_root/level_1_k1.conf"
        "level_1_k2": "conf_root/level_1_k2.conf"
    }
    """
    
    def write_stdout(self, cfg_data):
        print (json.dumps(cfg_data,indent=2))

if __name__ == '__main__':
    module_name = sys.argv[1] # Module name
    param_no_format_conv = sys.argv[2] #Consul KV json contains all values in string(including int and boolan). If you dont want to convert back to int and boolean give that Params in comma(,) separated
    conf_data = sys.argv[3] #json data
    writer = CfgWriter()

    conv = Convertor()

    conv_data = conv.convert_conf(conf_data)
    writer.write_stdout(conv_data)

