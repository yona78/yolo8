import os
import tempfile
from kafka import KafkaConsumer, KafkaProducer
import boto3
import cv2
from ultralytics import YOLO

KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
INPUT_TOPIC = os.getenv('INPUT_TOPIC', 'video_paths')
OUTPUT_TOPIC = os.getenv('OUTPUT_TOPIC', 'processed_videos')
S3_BUCKET = os.getenv('S3_BUCKET', 'videos')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

s3 = boto3.client('s3', region_name=AWS_REGION)
consumer = KafkaConsumer(INPUT_TOPIC, bootstrap_servers=[KAFKA_BROKER])
producer = KafkaProducer(bootstrap_servers=[KAFKA_BROKER])
model = YOLO('yolov8n.pt')


def process_video(s3_key: str) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, os.path.basename(s3_key))
        output_path = os.path.join(tmpdir, f"tracked_{os.path.basename(s3_key)}")
        s3.download_file(S3_BUCKET, s3_key, input_path)

        cap = cv2.VideoCapture(input_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        cap.release()

        writer = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))

        for result in model.track(source=input_path, stream=True, tracker='bytetrack.yaml'):
            frame = result.plot()
            writer.write(frame)
        writer.release()

        output_key = f"processed/{os.path.basename(output_path)}"
        s3.upload_file(output_path, S3_BUCKET, output_key)
        producer.send(OUTPUT_TOPIC, output_key.encode('utf-8'))
        producer.flush()


def main() -> None:
    for msg in consumer:
        s3_key = msg.value.decode('utf-8')
        try:
            process_video(s3_key)
        except Exception as exc:
            print(f"Error processing {s3_key}: {exc}")


if __name__ == "__main__":
    main()
