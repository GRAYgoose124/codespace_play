package main

import (
	"bytes"
	"encoding/gob"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync"
)

type FileMetadata struct {
	Path string
	Size int64
	//LastModified time.Time
	//checksum string
}

var index []FileMetadata

func indexFiles(startDir string) {
	filepath.Walk(startDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return nil // Ignore errors
		}
		if !info.IsDir() {
			index = append(index, FileMetadata{Path: path, Size: info.Size()})
		}
		return nil
	})
}

func saveIndexToFile(indexFile string) error {
	file, err := os.Create(indexFile)
	if err != nil {
		return err
	}
	defer file.Close()

	encoder := gob.NewEncoder(file)
	return encoder.Encode(index)
}

func loadIndexFromFile(indexFile string) error {
	file, err := os.ReadFile(indexFile)
	if err != nil {
		return err
	}

	decoder := gob.NewDecoder(bytes.NewReader(file))
	return decoder.Decode(&index)
}

type SearchQuery struct {
	Pattern string
	// Add other criteria if necessary
}

type SearchResult struct {
	File FileMetadata
	Err  error
}

func searchChunk(chunk []FileMetadata, query SearchQuery, results chan<- SearchResult) {
	for _, file := range chunk {
		if strings.Contains(file.Path, query.Pattern) {
			results <- SearchResult{File: file}
		}
	}
}

func searchFiles(query SearchQuery) []FileMetadata {
	chunkSize := len(index) / 32
	resultsChan := make(chan SearchResult)

	var wg sync.WaitGroup
	expectedResults := 0

	for i := 0; i < 32; i++ {
		start := i * chunkSize
		end := start + chunkSize
		if i == 31 {
			end = len(index)
		}

		expectedResults += end - start

		wg.Add(1)
		go func(start, end int) {
			defer wg.Done()
			searchChunk(index[start:end], query, resultsChan)
		}(start, end)
	}

	go func() {
		wg.Wait()
		close(resultsChan)
	}()

	var results []FileMetadata
	for i := 0; i < expectedResults; i++ {
		result := <-resultsChan
		if result.Err == nil {
			results = append(results, result.File)
		}
	}

	return results
}

func main() {
	const indexPath = "./index.gob"

	// Try loading the index from the file
	err := loadIndexFromFile(indexPath)
	if err != nil {
		// Index file doesn't exist or there was an error; build the index
		indexFiles("/home/grayson")
		// Save the index for subsequent runs
		err := saveIndexToFile(indexPath)
		if err != nil {
			fmt.Println("Error saving index:", err)
		}
	}

	// Search for files with a specific pattern
	query := SearchQuery{Pattern: ".py"}
	files := searchFiles(query)

	// print count first
	count := len(files)
	fmt.Println(count)

	if count < 1000 {
		for _, file := range files {
			fmt.Println(file.Path)
		}
	}

}
