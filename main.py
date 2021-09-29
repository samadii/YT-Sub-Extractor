from youtube_transcript_api import YouTubeTranscriptApi
import os
import pprint
import re
from urllib.parse import urlparse, parse_qs
import logging
from py_youtube import Data
from googleapiclient.http import MediaIoBaseDownload
import io

URLL = ''
def extract_video_id(url):
    global URLL
    yt = Data(f"{url}")
    URLL = yt.title()
    query = urlparse(url)
    if query.hostname == 'youtu.be': return query.path[1:]
    if query.hostname in ('www.youtube.com', 'youtube.com'):
        if query.path == '/watch': return parse_qs(query.query)['v'][0]
        if query.path[:7] == '/embed/': return query.path.split('/')[2]
        if query.path[:3] == '/v/': return query.path.split('/')[2]
    return None


def extract_channel_id(url):
    # https://www.youtube.com/channel/UCbhoJkMvEr-tBvTa18obndg
    query = urlparse(url)
    #print(query)
    #print(query.path.split('channel/')[1])
    return query.path.split('channel/')[1]


def get_video_comments(service, **kwargs):
    comments = []
    results = service.commentThreads().list(**kwargs).execute()
    while results:
        for item in results['items']:
            kind = item['kind']
            autorName = item['snippet']['topLevelComment']['snippet']['authorDisplayName']
            text = item['snippet']['topLevelComment']['snippet']['textDisplay'].strip("'")
            #comment = f"kind: {kind}, displayname: {autorName} , text: {text}"

            comments.append(text)
            break

        if 'nextPageToken' in results:
            kwargs['pageToken'] = results['nextPageToken']
            results = service.commentThreads().list(**kwargs).execute()
        else:
            break

    return comments



def get_available_lang(video_id):
    codes = []
    manual = []
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    for transcript in transcript_list:
        if not transcript.is_generated:
            manual.append(transcript.language)
            codes.append(transcript.language_code)
    return manual, codes


def fetch_man_chosen(video_id, lang):
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    target = transcript_list.find_manually_created_transcript(language_codes=[lang])
    dldir = f'{URLL}.txt'
    with open(dldir, 'w', encoding='utf-8') as f:
        for snippet in target.fetch():
            pprint.pprint(snippet)
            f.write(snippet['text']+' ')
    return dldir

def fetch_auto_chosen(video_id, lang):
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    target = transcript_list.find_generated_transcript(['en'])
    # if target:
    #     print(target)
    dldir = f'{URLL}.txt'
    if target:
        with open(dldir, 'w', encoding='utf-8') as f:
            for snippet in target.translate('uk').fetch():
                pprint.pprint(snippet)
                f.write(snippet['text'] + '\n')
        return dldir
    else:
        return None



if __name__ == '__main__':
    video_id = extract_video_id("https://www.youtube.com/watch?v=RPAW5A7vvD4")
    comentator_chanel_id = extract_channel_id("https://www.youtube.com/channel/UCbhoJkMvEr-tBvTa18obndg")
    varlamov_chanel_id = extract_channel_id("https://www.youtube.com/channel/UC90g4p7XhSEw0r1qIiuq0rQ")
    cap_video = extract_video_id("https://www.youtube.com/watch?v=wfNX1cHk-fE")

    fetch_auto_chosen(cap_video, 'uk')



