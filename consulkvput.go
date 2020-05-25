package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io/ioutil"
	"path/filepath"
	"strconv"
)

var kvs []*KV

// Utility code to populate Consul KV store and also extract the KV pair to JSON format

// KV represents a KV pair
type KV struct {
	Key   string
	Value string
}

// traverse takes json from ToKVs function and returns a list of KV pairs where each key is a path in the Consul KV store
func traverse(path string, j interface{}) ([]*KV, error) {
	kvs := make([]*KV, 0)

	pathPre := ""
	if path != "" {
		pathPre = path + "/"
	}

	switch j.(type) {
	case []interface{}:
		for sk, sv := range j.([]interface{}) {
			temp := strconv.Itoa(sk)
			skvs, err := traverse(pathPre+temp, sv)
			if err != nil {
				return nil, err
			}
			kvs = append(kvs, skvs...)
		}
	case map[string]interface{}:
		for sk, sv := range j.(map[string]interface{}) {
			skvs, err := traverse(pathPre+sk, sv)
			if err != nil {
				return nil, err
			}
			kvs = append(kvs, skvs...)
		}
	case float64:
		kvs = append(kvs, &KV{Key: path, Value: strconv.FormatFloat(j.(float64), 'f', -1, 64)})
	case bool:
		kvs = append(kvs, &KV{Key: path, Value: strconv.FormatBool(j.(bool))})
	case nil:
		kvs = append(kvs, &KV{Key: path, Value: ""})
	default:
		kvs = append(kvs, &KV{Key: path, Value: j.(string)})
	}

	return kvs, nil
}

func updateConfig(dir string, fileName string, outputDir string, merge bool) error {
	fpath := filepath.Join(dir, fileName)

	data, err := ioutil.ReadFile(fpath)
	if err != nil {
		return err
	}
	if merge == true {
		ToKVs(data)
	} else {
		kvs = make([]*KV, 0)
		entries, err := ToKVs(data)
		for _, kv := range entries {
			fmt.Printf("%s, %s\n", kv.Key, kv.Value)
		}
		if err != nil {
			fmt.Println(err)
		}
	}
	return nil
}

// ToKVs takes a json byte array and returns a list of KV pairs where each key is a path in the Consul KV store
func ToKVs(jsonData []byte) ([]*KV, error) {
	var i interface{}
	err := json.Unmarshal(jsonData, &i)
	if err != nil {
		return nil, err
	}
	m := i.(map[string]interface{})
	return traverse("", m)
}

func main() {
	dir := flag.String("in", "/tmp/", "a string")
	file := flag.String("file", "sample.json", "a string")
	outputDir := flag.String("out", "/tmp/output", "a string")
	merge := flag.Bool("merge", false, "a bool")
	updateConfig(*dir, *file, *outputDir, *merge)
}
