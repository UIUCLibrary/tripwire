======================
Using the Command Line
======================

Getting Help
============

To get help at any point you can use the `--help` flag

.. code-block:: shell-session

    user@WORKMACHINE123 tripwire % tripwire --help
    usage: tripwire [-h] [--version] {get-hash,validate-checksums} ...

    options:
      -h, --help            show this help message and exit
      --version             show program's version number and exit

    subcommands:
      {get-hash,manifest-check,validate-checksums}


Get Hash
========

To get the hash value of a file, use the `get-hash` command. This will return the hash value of the file in the format
`<filename> --> <hash type>: <hash value>`.

.. code-block:: shell-session

    user@WORKMACHINE123 % tripwire get-hash somefile.wav
    somefile.wav --> md5: d41d8cd98f00b204e9800998ecf8427e


Validate Checksums
==================

To validate checksums for files in a directory, use the `validate-checksums` command. This search for all files within
a given path and search for a checksum file. The checksum file must be in the same directory as the files to be
validated. If the checksum does not match the expected value, you will get notified.

.. code-block:: shell-session

    user@WORKMACHINE123 % tripwire validate-checksums /path/to/directory

Manifest Check
==============

Added in version 0.2.1

To check a manifest file against a directory, use the `manifest-check` command. This will check the files in the
manifest are present in the directory and show any files that are not supposed to be there.

Usage format: tripwire manifest-check <manifest_file> <search_path>

example:

.. code-block:: shell-session

    user@WORKMACHINE123 % tripwire manifest-check ./manifest-film.tsv ./sample_package/film
    Line: 7. Unable to locate: 2803015_film2of5_UIUCvUSC_FB_Sept1989_label.jpg

    Files found that were not included in manifest:
    * otherfile.txt

.. note::
    This will not use a excel file as a manifest. You will have to export the Excel file to a tab separated file first.

Metadata
========

This command contains two subcommands: `show` and `validate`.

show
----

This subcommand, `show`, displays metadata for files using MediaInfo.

example usage:

This example shows how to show metadata for all .wav files in a directory regardless of depth.

.. code-block:: shell-session

    user@WORKMACHINE123 % tripwire metadata show "/Volumes/G-RAID with Thunderbolt/sample data/media/UIUC_0028/**/*.wav"

    ====================================================================================================================
    file: /Volumes/G-RAID with Thunderbolt/sample data/media/UIUC_0028/Preservation/28_pres_01.wav

    metadata:
    {'tracks': [{'audio_channels_total': '2',
                 'audio_codecs': 'PCM',
                 'audio_format_list': 'PCM',
                 'audio_format_withhint_list': 'PCM',
                 'bext_present': 'Yes',
                 'bext_version': '1',
                 'commercial_name': 'Wave',
                 'complete_name': '/Volumes/G-RAID with Thunderbolt/sample data/media/UIUC_0028/Preservation/28_pres_01.wav',
                 'count': '351',
                 'count_of_audio_streams': '1',
                 'count_of_stream_of_this_kind': '1',
                 'duration': 1329152,
                 'encoded_date': '2024-12-23 11:04:02',
                 'encoding_settings': 'A=ANALOGUE,F=96000,W=24,M=stereo,T=Player:A807-06;Brand:Studer;Model:A807MK2,SN:15118 / '
                                      'A=PCM,F=96000,W=24,M=stereo,T=Converter:MYTEK-02;Brand:Mytek;Model:8X192 ADDA,SN:01504-0906-025 / '
                                      'A=PCM,F=96000,W=24,M=stereo,T=Encoder:MIS-AUDIO-06-05;Brand:;Model:,SN:',
                 'file_creation_date': '2025-07-29 17:13:15 UTC',
                 'file_creation_date__local': '2025-07-29 12:13:15',
                 'file_extension': 'wav',
                 'file_last_modification_date': '2025-07-29 22:12:00 UTC',
                 'file_last_modification_date__local': '2025-07-29 17:12:00',
                 'file_name': '28_pres_01',
                 'file_name_extension': '28_pres_01.wav',
                 'file_size': 765592500,
                 'folder_name': '/Volumes/G-RAID with Thunderbolt/sample data/media/UIUC_0028/Preservation',
                 'format': 'Wave',
                 'format_extensions_usually_used': 'act at9 wav',
                 'format_settings': 'PcmWaveformat',
                 'internet_media_type': 'audio/vnd.wave',
                 'kind_of_stream': 'General',
                 'other_duration': ['22 min 9 s', '22 min 9 s 152 ms', '22 min 9 s', '00:22:09.152', '00:22:09.152'],
                 'other_file_size': ['730 MiB', '730 MiB', '730 MiB', '730 MiB', '730.1 MiB'],
                 'other_format': ['Wave'],
                 'other_kind_of_stream': ['General'],
                 'other_overall_bit_rate': ['4 608 kb/s'],
                 'other_overall_bit_rate_mode': ['Constant'],
                 'other_stream_size': ['948 Bytes (0%)', '948 Bytes', '948 Bytes', '948 Bytes', '948.0 Bytes', '948 Bytes (0%)'],
                 'overall_bit_rate': 4608006,
                 'overall_bit_rate_mode': 'CBR',
                 'proportion_of_this_stream': '0.00000',
                 'stream_identifier': '0',
                 'stream_size': 948,
                 'track_type': 'General'},
                {'bit_depth': 24,
                 'bit_rate': 4608000,
                 'bit_rate_mode': 'CBR',
                 'channel_s': 2,
                 'codec_id': '1',
                 'codec_id_url': 'http://www.microsoft.com/windows/',
                 'commercial_name': 'PCM',
                 'count': '285',
                 'count_of_stream_of_this_kind': '1',
                 'delay': '0.000000',
                 'delay__origin': 'Container (bext)',
                 'duration': 1329152,
                 'format': 'PCM',
                 'format_settings': 'Little / Signed',
                 'format_settings__endianness': 'Little',
                 'format_settings__sign': 'Signed',
                 'kind_of_stream': 'Audio',
                 'other_bit_depth': ['24 bits'],
                 'other_bit_rate': ['4 608 kb/s'],
                 'other_bit_rate_mode': ['Constant'],
                 'other_channel_s': ['2 channels'],
                 'other_delay': ['00:00:00.000', '00:00:00.000'],
                 'other_delay__origin': ['Container (bext)'],
                 'other_duration': ['22 min 9 s', '22 min 9 s 152 ms', '22 min 9 s', '00:22:09.152', '00:22:09.152'],
                 'other_format': ['PCM'],
                 'other_kind_of_stream': ['Audio'],
                 'other_sampling_rate': ['96.0 kHz'],
                 'other_stream_size': ['730 MiB (100%)', '730 MiB', '730 MiB', '730 MiB', '730.1 MiB', '730 MiB (100%)'],
                 'proportion_of_this_stream': '1.00000',
                 'samples_count': '127598592',
                 'sampling_rate': 96000,
                 'stream_identifier': '0',
                 'stream_size': 765591552,
                 'track_type': 'Audio'}]}
