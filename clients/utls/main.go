package main

import (
	"bytes"
	ctls "crypto/tls"
	"context"
	"flag"
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"strings"
	"time"

	tls "github.com/refraction-networking/utls"
	"golang.org/x/net/http2"
)

func utlsConn(ctx context.Context, network, addr string) (net.Conn, error) {
	dialer := &net.Dialer{Timeout: 10 * time.Second}
	raw, err := dialer.DialContext(ctx, network, addr)
	if err != nil {
		return nil, err
	}
	host := addr
	if i := strings.LastIndex(addr, ":"); i > 0 {
		host = addr[:i]
	}
	cfg := &tls.Config{ServerName: strings.Trim(host, "[]"), InsecureSkipVerify: false}
	u := tls.UClient(raw, cfg, tls.HelloChrome_Auto)
	if err := u.Handshake(); err != nil {
		raw.Close()
		return nil, err
	}
	return u, nil
}

func main() {
	base := flag.String("base", "https://127.0.0.1/potato_h2", "base url")
	cid := flag.String("client-id", "node1", "client id")
	send := flag.String("send", "", "payload to send")
	recv := flag.Bool("recv", false, "receive payload")
	cafile := flag.String("cafile", "", "CA cert")
	flag.Parse()

	tr := &http2.Transport{}
	tr.DialTLSContext = func(ctx context.Context, network, addr string, cfg *ctls.Config) (net.Conn, error) {
		return utlsConn(ctx, network, addr)
	}
	_ = *cafile
	client := &http.Client{Transport: tr, Timeout: 10 * time.Second}

	if *send != "" {
		req, _ := http.NewRequest(http.MethodPost, *base+"/send", bytes.NewBufferString(*send))
		req.Header.Set("X-Client-Id", *cid)
		resp, err := client.Do(req)
		if err != nil {
			fmt.Println("send error:", err)
			os.Exit(1)
		}
		defer resp.Body.Close()
		body, _ := io.ReadAll(resp.Body)
		fmt.Println(resp.StatusCode, string(body))
	}

	if *recv {
		req, _ := http.NewRequest(http.MethodGet, *base+"/recv", nil)
		req.Header.Set("X-Client-Id", *cid)
		resp, err := client.Do(req)
		if err != nil {
			fmt.Println("recv error:", err)
			os.Exit(1)
		}
		defer resp.Body.Close()
		body, _ := io.ReadAll(resp.Body)
		fmt.Println(resp.StatusCode, string(body))
	}
}
