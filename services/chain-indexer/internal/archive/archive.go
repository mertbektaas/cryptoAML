package archive

import (
	"bytes"
	"compress/gzip"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"

	"github.com/aws/aws-sdk-go-v2/aws"
	awsconfig "github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/s3"
	"github.com/mertbektaas/cryptoaml/chain-indexer/internal/model"
)

type Writer interface {
	Put(context.Context, string, model.RawEnvelope) error
}

type FileWriter struct{ Root string }

func (w FileWriter) Put(_ context.Context, key string, envelope model.RawEnvelope) error {
	data, err := marshalGzip(envelope)
	if err != nil {
		return err
	}
	path := filepath.Join(w.Root, filepath.Clean(key))
	if !strings.HasPrefix(path, filepath.Clean(w.Root)+string(os.PathSeparator)) {
		return fmt.Errorf("archive key escapes root")
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o750); err != nil {
		return fmt.Errorf("create archive directory: %w", err)
	}
	return os.WriteFile(path, data, 0o640)
}

type S3Writer struct {
	Client *s3.Client
	Bucket string
}

func NewS3Writer(ctx context.Context, endpoint, region, bucket, accessKey, secretKey string) (*S3Writer, error) {
	if endpoint == "" || bucket == "" {
		return nil, fmt.Errorf("s3 endpoint and bucket are required")
	}
	if region == "" {
		region = "garage"
	}
	creds := aws.NewCredentialsCache(staticCredentials{accessKey: accessKey, secretKey: secretKey})
	load, err := awsconfig.LoadDefaultConfig(ctx, awsconfig.WithRegion(region), awsconfig.WithCredentialsProvider(creds))
	if err != nil {
		return nil, err
	}
	client := s3.NewFromConfig(load, func(o *s3.Options) { o.BaseEndpoint = aws.String(endpoint); o.UsePathStyle = true })
	return &S3Writer{Client: client, Bucket: bucket}, nil
}

func (w *S3Writer) Put(ctx context.Context, key string, envelope model.RawEnvelope) error {
	data, err := marshalGzip(envelope)
	if err != nil {
		return err
	}
	_, err = w.Client.PutObject(ctx, &s3.PutObjectInput{Bucket: aws.String(w.Bucket), Key: aws.String(key), Body: bytes.NewReader(data), ContentType: aws.String("application/json"), ContentEncoding: aws.String("gzip")})
	return err
}

type staticCredentials struct{ accessKey, secretKey string }

func (c staticCredentials) Retrieve(context.Context) (aws.Credentials, error) {
	return aws.Credentials{AccessKeyID: c.accessKey, SecretAccessKey: c.secretKey}, nil
}

func marshalGzip(value any) ([]byte, error) {
	var raw bytes.Buffer
	enc := json.NewEncoder(&raw)
	enc.SetEscapeHTML(false)
	if err := enc.Encode(value); err != nil {
		return nil, err
	}
	var out bytes.Buffer
	zw := gzip.NewWriter(&out)
	if _, err := io.Copy(zw, &raw); err != nil {
		return nil, err
	}
	if err := zw.Close(); err != nil {
		return nil, err
	}
	return out.Bytes(), nil
}
