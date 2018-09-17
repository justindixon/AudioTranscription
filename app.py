#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import io
import json
import os
import re
import subprocess
import sys
import natsort
import six

from google.cloud import language_v1, speech
from google.cloud.language_v1 import enums as enums_lan
from google.cloud.speech import enums, types


# option to either return additional sentimental analysis
def sentimentAnalysis(trascribedFile):

    client = language_v1.LanguageServiceClient()

    content = trascribedFile

    if isinstance(content, six.binary_type):
        content = content.decode('utf-8')

    type_ = enums.Document.Type.PLAIN_TEXT
    document = {'type': type_, 'content': content}

    response = client.analyze_sentiment(document)
    sentiment = response.document_sentiment
    print('Score: {}'.format(sentiment.score))
    print('Magnitude: {}'.format(sentiment.magnitude))


def transcribe(audioFile):

    # Instantiates a client
    client = speech.SpeechClient.from_service_account_json('/home/justin/2gbProject/Natural Language-ad18f251cc00.json')

    # Set up the config info
    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code='en-US'
        )

    # Need to check the size, type of the file  
    # For type need to convert file into a usuable part
    
    print('Converting: ', audioFile)
    subprocess.call('mkdir temp', shell=True)
    process = subprocess.Popen(['ffmpeg',  '-i', audioFile, '-acodec', 'pcm_s16le', '-ac', '1', '-ar', '16000', 'output.wav'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    stdout, stderr = process.communicate()

    # Split up the file into smaller files
    print('Splitting up the Audio File into smaller parts')
    subprocess.call('sox output.wav ./temp/outputfile.wav trim 0 15 : newfile : restart', shell=True)    
    
    # Get list of split up files to transcribe
    filesToTranscribe = natsort.natsorted(os.listdir("./temp/"))

    # Send the smaller files to be transcibed and combine the results into one large file
    # Open file to combine all the files
    print('Transcribing the Audio File')
    transcript = []
    for segments in filesToTranscribe:
        try:
            segmentName = "./temp/" + segments 
            with io.open(segmentName, 'rb') as audio_file:
                content = audio_file.read()
                audio = types.RecognitionAudio(content=content)
                          
            config = types.RecognitionConfig(
                encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code='en-US')
                
            response = client.recognize(config, audio)
            for result in response.results:
                transcript.append(result.alternatives[0].transcript)
        except:
            print('Oops! That segment didn\'t work: ' + segmentName)
    # Delete the temp files and folder
    subprocess.call('rm -r ./temp/', shell=True)
    subprocess.call('rm output.wav', shell=True)
    # Finally return the transcript
    return transcript
    


def main():
    parser = argparse.ArgumentParser(description='Transcription AI.')
    parser.add_argument('--audioFile', required=True,
                        help='Path to the audio file')
    parser.add_argument('--sentiment', required=False,
                        help='Returns the sentiment analysis of the audio file')
    args = parser.parse_args()
    
    # Return JSON response
    transcript = transcribe(args.audioFile)

    """if args.sentiment:
        sentiment = sentimentAnalysis(transcript)
    else:"""
    sentiment = None

    print(json.dumps({'file': args.audioFile, 'transcript': transcript, 'sentiment': sentiment},
        sort_keys=True, indent=4))

if __name__ == '__main__':
    main()
