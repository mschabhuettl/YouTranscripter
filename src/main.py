# Import required modules
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from youtube_transcript_api import YouTubeTranscriptApi
import os
import re

# Ask for user input for API key, channel ID, and preferred languages
API_KEY = input("Please enter your YouTube API key: ")
CHANNEL_ID = input("Please enter the YouTube Channel ID: ")
PREFERRED_LANGUAGES = input("Please enter preferred languages for transcripts (separated by comma, e.g., 'de,en'): ").split(',')

YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'
transcript_dir = 'transcripts'
os.makedirs(transcript_dir, exist_ok=True)


def get_channel_videos(channel_id):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)
    channel_response = youtube.channels().list(id=channel_id, part='contentDetails').execute()
    playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    videos = []
    next_page_token = None
    while True:
        playlistitems_response = youtube.playlistItems().list(
            playlistId=playlist_id,
            part='snippet',
            maxResults=50,
            pageToken=next_page_token
        ).execute()
        for playlist_item in playlistitems_response['items']:
            video_id = playlist_item['snippet']['resourceId']['videoId']
            videos.append(f'https://www.youtube.com/watch?v={video_id}')
        next_page_token = playlistitems_response.get('nextPageToken')
        if not next_page_token:
            break
    return videos


def write_videos_to_file(videos, filename):
    with open(filename, 'w') as file:
        for video in videos:
            file.write(video + '\n')


def get_video_title(video_id):
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    request = youtube.videos().list(part="snippet", id=video_id)
    response = request.execute()
    if response["items"]:
        return response["items"][0]["snippet"]["title"]
    else:
        return "Unbekannter Titel"


def sanitize_filename(text):
    text = re.sub(r'[\\/*?:"<>|]', "", text)
    text = text.replace(' ', '_')
    return text[:50]


def fetch_and_save_transcripts(video_file):
    with open(video_file, 'r') as f:
        for line in f:
            video_id = line.strip().split('=')[-1]
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=PREFERRED_LANGUAGES)
                transcript_text = '\n'.join([item['text'] for item in transcript])
                video_title = get_video_title(video_id)
                sanitized_title = sanitize_filename(video_title)
                filename = f"{sanitized_title}_{video_id}.txt"
                filepath = os.path.join(transcript_dir, filename)
                with open(filepath, 'w', encoding='utf-8') as outfile:
                    outfile.write(f'Title: {video_title}\n\n')
                    outfile.write(transcript_text)
            except Exception as e:
                print(f'Error fetching transcript for video {video_id}: {e}')


def group_transcripts():
    output_file_path = 'gesammelte_transkripte.txt'
    divider = '\n\n' + '*' * 40 + '\n\n'
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        for filename in os.listdir(transcript_dir):
            if filename.endswith('.txt'):
                file_path = os.path.join(transcript_dir, filename)
                with open(file_path, 'r', encoding='utf-8') as input_file:
                    output_file.write(f'--- {filename} ---\n\n')
                    output_file.write(input_file.read())
                    output_file.write(divider)


def save_transcripts_in_batches():
    output_base_filename = 'gesammelte_transkripte'
    max_transcripts_per_file = 500
    batch_counter = 1
    transcript_counter = 0
    output_file = None
    for filename in sorted(os.listdir(transcript_dir)):
        if filename.endswith('.txt'):
            if transcript_counter % max_transcripts_per_file == 0:
                if output_file:
                    output_file.close()
                output_filename = f"{output_base_filename}_{batch_counter}.txt"
                output_file = open(output_filename, 'w', encoding='utf-8')
                batch_counter += 1
            file_path = os.path.join(transcript_dir, filename)
            with open(file_path, 'r', encoding='utf-8') as input_file:
                output_file.write(input_file.read() + '\n\n' + '*' * 40 + '\n\n')
                transcript_counter += 1
    if output_file:
        output_file.close()


def process_youtube_channel():
    while True:
        print("\nYouTube Channel Processing Workflow")
        print("1. Download video links")
        print("2. Fetch and save transcripts")
        print("3. Group transcripts into a single file")
        print("4. Save transcripts in batches")
        print("5. Exit")
        
        choice = input("Enter your choice (1-5): ")
        
        if choice == '1':
            videos = get_channel_videos(CHANNEL_ID)
            write_videos_to_file(videos, 'youtube_videos.txt')
            print("Video links downloaded successfully.")
        elif choice == '2':
            fetch_and_save_transcripts('youtube_videos.txt')
            print("Transcripts fetched and saved successfully.")
        elif choice == '3':
            group_transcripts()
            print("Transcripts grouped into a single file successfully.")
        elif choice == '4':
            save_transcripts_in_batches()
            print("Transcripts saved in batches successfully.")
        elif choice == '5':
            print("Exiting...")
            break
        else:
            print("Invalid choice, please choose again.")


if __name__ == "__main__":
    process_youtube_channel()
