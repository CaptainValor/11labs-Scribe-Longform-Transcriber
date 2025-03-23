# ElevenLabs Scribe Longform Transcriber

A web application that transcribes long-form audio files using the ElevenLabs Scribe API. It automatically splits audio files into segments, transcribes each segment, and combines the transcripts with speaker detection.

## Disclaimer

This tool is intended to be run locally on your own machine. It was originally created by me (Stephen Torrence) on a Mac using Cursor and Claude. 

**No support or warranty is provided** - I'm sharing this publicly for anyone who might find it valuable, but cannot offer technical support or guarantee its functionality in all environments.

If you find it valuable, feel free donate a little something to me here: [PayPal](https://www.paypal.com/paypalme/ecotexan) [Venmo](https://account.venmo.com/u/stephen-torrence-1)

## Features

- **Long-form Audio Support**: Handles audio files of any length by automatically splitting them into manageable segments.
- **Speaker Diarization**: Identifies different speakers in your audio.
- **Speaker Labeling**: Allows you to label speakers for more readable transcripts.
- **Automatic Overlap Handling**: Includes overlap between segments to ensure continuity.
- **Clean, Modern Interface**: Simple and intuitive UI for easy uploading and transcription.
- **Progress Tracking**: Real-time status updates during the transcription process.
- **Customizable Settings**: Control diarization and specify the number of speakers.

## Requirements

- Python 3.7+
- Flask
- An ElevenLabs API key with Scribe access (obtain from [elevenlabs.io](https://elevenlabs.io))
- Required Python libraries: See requirements below

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/11labs-Scribe-Longform-Transcriber.git
   cd 11labs-Scribe-Longform-Transcriber
   ```

2. Install the required dependencies:
   ```
   pip install flask pydub requests
   ```

3. Run the application:
   ```
   python app.py
   ```

4. Open your browser and navigate to `http://localhost:5000`

## Usage

1. **Enter your ElevenLabs API Key** - You need an API key with Scribe access from [elevenlabs.io/account](https://elevenlabs.io/account)

2. **Configure Transcription Settings**:
   - Toggle speaker diarization on/off
   - Optionally specify the number of speakers (helps improve accuracy)

3. **Upload Audio File**:
   - Drag and drop your audio file or click to browse
   - Supported formats: MP3, WAV, M4A, etc. (any format supported by pydub)

4. **Transcribe**:
   - Click the "Transcribe" button to start the process
   - Monitor progress in real-time

5. **Label Speakers**:
   - Once the initial transcript is ready, you can customize speaker labels
   - Click "Process Transcript" to apply your labels

6. **View Final Transcript**:
   - The final transcript will be displayed with your custom speaker labels

## How It Works

1. The application splits your audio file into segments (default: 8-minute segments with 10-second overlaps)
2. Each segment is sent to the ElevenLabs Scribe API for transcription
3. The responses are processed to merge the segments, handling the overlaps
4. Speaker diarization information is preserved and presented for customization
5. The final transcript combines all segments with your preferred speaker labels

## Privacy & Security

- Your audio files and transcripts remain on your local server and are not stored permanently
- Your API key is used only for communicating with ElevenLabs and is not stored or logged
- All temporary files are cleaned up after processing

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the [MIT License](LICENSE).

## Acknowledgements

- Built with [ElevenLabs Scribe API](https://elevenlabs.io/scribe)
- Uses Flask for the web framework
