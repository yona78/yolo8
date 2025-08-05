# YOLOv8 Kafka Tracking Service

This microservice listens to a Kafka topic for messages containing paths to video files stored in Amazon S3. For each video it downloads the file, runs a pre-trained YOLOv8 model to detect and track objects, draws bounding boxes with class labels and tracking IDs, then uploads the annotated video back to S3 and publishes the output key to another Kafka topic.

Object IDs are assigned using the default [ByteTrack](https://github.com/ifzhang/ByteTrack) tracker built into Ultralytics YOLO. Frames are processed headlessly (`show=True` is not used), making the service suitable for server environments. The annotated video and Kafka notification are produced only when at least one object is detected in the input.

## Requirements

- Python 3.8+
- Access to a Kafka broker
- AWS credentials with access to the desired S3 bucket
- Dependencies listed in `requirements.txt`

## Usage

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set environment variables for your setup:
   ```bash
   export KAFKA_BROKER=localhost:9092
   export INPUT_TOPIC=video_paths
   export OUTPUT_TOPIC=processed_videos
   export S3_BUCKET=your-bucket
   export AWS_REGION=us-east-1
   # AWS credentials can be provided via environment variables or IAM roles
   ```
3. Start the service:
   ```bash
   python service.py
   ```

Messages consumed from the `INPUT_TOPIC` should contain the S3 object key for a video file. The processed video is uploaded to the same bucket under a `processed/` prefix and the new key is published to the `OUTPUT_TOPIC`.
