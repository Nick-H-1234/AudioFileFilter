import audio_metadata
import os
import shutil
import sys
import argparse

BITRATE_DEFAULT = 1000000
AUDIO_SUFFIXES = ("mp3", "m4a", "ogg", "wav")

def noMusic(files):
    for file in files:
        if file.endswith(AUDIO_SUFFIXES):
            return False
    return True

def hasSubDirectories(path, files):
    for file in files:
        filepath = os.path.join(path, file)
        if os.path.isdir(filepath):
            return True
    return False

# tidy up
def removeEmptyFolders(path, removeRoot=True):
    if not os.path.isdir(path):
        return

    # recursively remove empty subfolders
    files = os.listdir(path)
    if len(files):
        for f in files:
            fullpath = os.path.join(path, f)
            if os.path.isdir(fullpath):
                removeEmptyFolders(fullpath)

    # check if folder contains no music and no sub-folders
    deleteThis = False
    files = os.listdir(path)
    if len(files) == 0 and removeRoot:
        deleteThis = True
    elif hasSubDirectories(path, files):
        pass
    elif noMusic(files):
        deleteThis = True

    if deleteThis:
        print("Removing empty folder:", path)
        shutil.rmtree(path)

def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("infolder", help="the input directory")
    parser.add_argument("outfolder", help="the output folders")
    parser.add_argument("-b", type=int, help="the bitrate threshold")
    args = parser.parse_args()
    if args.b is None:
        bitrate_threshold = BITRATE_DEFAULT
    else:
        bitrate_threshold = args.b
    startDir = args.infolder
    highOutputRoot = os.path.join(args.outfolder, "highoutput")
    lowOutputRoot = os.path.join(args.outfolder, "lowoutput")

    if not os.path.isdir(highOutputRoot):
        os.mkdir(highOutputRoot)
    if not os.path.isdir(lowOutputRoot):
        os.mkdir(lowOutputRoot)

    for root, dirs, files in os.walk(startDir):
        highDir = os.path.join(highOutputRoot, os.path.relpath(root, startDir))
        lowDir = os.path.join(lowOutputRoot, os.path.relpath(root, startDir))
        if not os.path.isdir(highDir):
            os.mkdir(highDir)
        if not os.path.isdir(lowDir):
            os.mkdir(lowDir)

        for file in files:
            filepath = os.path.join(root,file)
            if file.endswith("m4a"):
                # m4a not supported by audio-metadata library so just copy into high bitrate directory anyway.
                file_metadata = audio_metadata.load(filepath)
                shutil.copy(filepath, highDir)
                continue
            if not file.endswith(AUDIO_SUFFIXES):
                shutil.copy(filepath, highDir)
                shutil.copy(filepath, lowDir)
                continue

            try:
                file_metadata = audio_metadata.load(filepath)
                if file_metadata.streaminfo.bitrate >= bitrate_threshold:
                    shutil.copy(filepath, highDir)
                else:
                    shutil.copy(filepath, lowDir)

            except (audio_metadata.UnsupportedFormat) as e:
                # copy to both output directories
                print("Unsupported Format found", file, e)
                shutil.copy(filepath, highDir)
                shutil.copy(filepath, lowDir)
            except IOError as e:
                print("IOError. %s" %e)
            except:
                print("unknown error:", sys.exc_info())

    removeEmptyFolders(lowOutputRoot, False)
    removeEmptyFolders(highOutputRoot, False)


if __name__ == '__main__':
    main(sys.argv[1:])