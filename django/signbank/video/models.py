""" Models for the video application
keep track of uploaded videos and converted versions
"""

from django.db import models
from django.conf import settings
import sys, os, time, shutil

from signbank.video.convertvideo import extract_frame, convert_video, ffmpeg

from django.core.files.storage import FileSystemStorage
from django.contrib.auth import models as authmodels
# from django.contrib.auth.models import User
from datetime import datetime

from signbank.dictionary.models import *

class Video(models.Model):
    """A video file stored on the site"""

    # video file name relative to MEDIA_ROOT
    videofile = models.FileField("Video file in h264 mp4 format", upload_to=settings.VIDEO_UPLOAD_LOCATION)

    def __str__(self):
        return self.videofile.name

    def process(self):
        """The clean method will try to validate the video
        file format, optimise for streaming and generate
        the poster image"""

        self.poster_path()
        # self.ensure_mp4()


    def poster_path(self, create=True):
        """Return the path of the poster image for this
        video, if create=True, create the image if needed
        Return None if create=False and the file doesn't exist"""

        vidpath, ext = os.path.splitext(self.videofile.path)
        poster_path = vidpath + ".jpg"

        if not os.path.exists(poster_path):
            if create:
                # need to create the image
                extract_frame(self.videofile.path, poster_path)
            else:
                return None

        return poster_path


    def poster_url(self):
        """Return the URL of the poster image for this video"""

        # generate the poster image if needed
        path = self.poster_path()

        # splitext works on urls too!
        vidurl, ext = os.path.splitext(self.videofile.url)
        poster_url = vidurl + ".jpg"

        return poster_url


    def get_absolute_url(self):
        return self.videofile.url


    def ensure_mp4(self):
        """Ensure that the video file is an h264 format
        video, convert it if necessary"""

        # convert video to use the right size and iphone/net friendly bitrate
        # create a temporary copy in the new format
        # then move it into place

        # print "ENSURE: ", self.videofile.path

        (basename, ext) = os.path.splitext(self.videofile.path)
        tmploc = basename + "-conv.mp4"
        err = convert_video(self.videofile.path, tmploc, force=True)
        # print tmploc
        shutil.move(tmploc, self.videofile.path)


    def delete_files(self):
        """Delete the files associated with this object"""

        try:
            os.unlink(self.videofile.path)
            poster_path = self.poster_path(create=False)
            if poster_path:
                os.unlink(poster_path)
        except:
            pass


import shutil

class GlossVideoStorage(FileSystemStorage):
    """Implement our shadowing video storage system"""

    def __init__(self, location=settings.MEDIA_ROOT, base_url=settings.MEDIA_URL):
        super(GlossVideoStorage, self).__init__(location, base_url)


    def get_valid_name(self, name):
        """Generate a valid name, we use directories named for the
        first two digits in the filename to partition the videos"""

        (targetdir, basename) = os.path.split(name)

        path = os.path.join(str(basename)[:2], str(basename))

        result = os.path.join(targetdir, path)

        return result


storage = GlossVideoStorage()

# The 'action' choices are used in the GlossVideoHistory class
ACTION_CHOICES = (('delete', 'delete'),
                  ('upload', 'upload'),
                  ('rename', 'rename'),
                  ('watch', 'watch'),
                  )


class GlossVideoHistory(models.Model):
    """History of video uploading and deletion"""

    action = models.CharField("Video History Action",max_length=6, choices=ACTION_CHOICES, default='watch')
    # When was this action done?
    datestamp = models.DateTimeField("Date and time of action", auto_now_add=True)  # WAS: default=datetime.now()
    # See 'vfile' in video.views.addvideo
    uploadfile = models.TextField("User upload path", default='(not specified)')
    # See 'goal_location' in addvideo
    goal_location = models.TextField("Full target path", default='(not specified)')

    # WAS: Many-to-many link: to the user that has uploaded or deleted this video
    # WAS: actor = models.ManyToManyField("", User)
    # The user that has uploaded or deleted this video
    actor = models.ForeignKey(authmodels.User)

    # One-to-many link: to the Gloss in dictionary.models.Gloss
    gloss = models.ForeignKey(Gloss)

    def __str__(self):

        # Basic feedback from one History item: gloss-action-date
        name = self.gloss.idgloss + ': ' + self.action + ', (' + str(self.datestamp) + ')'
        return name.encode('ascii', errors='replace')

    class Meta:
        ordering = ['datestamp']


def sinal_upload_path(instance, filename):
    # o arquivo será salvo em MEDIA_ROOT/sinal_videos/originais/<filename>
    return settings.GLOSS_VIDEO_DIRECTORY+'/%s/%s' %(instance.gloss.idgloss[:2], filename)

class GlossVideo(models.Model):
    """A video that represents a particular idgloss"""

    videofile = models.FileField("video file", upload_to=sinal_upload_path)
    gloss = models.ForeignKey(Gloss)

    def process(self):
        """The clean method will try to validate the video
        file format, optimise for streaming and generate
        the poster image"""

        self.poster_path()
        # self.ensure_mp4()

    def poster_path(self, create=True):
        """Return the path of the poster image for this
        video, if create=True, create the image if needed
        Return None if create=False and the file doesn't exist"""

        vidpath, ext = os.path.splitext(self.videofile.path)
        poster_path = vidpath + ".jpg"

        if not os.path.exists(poster_path):
            if create:
                # need to create the image
                extract_frame(self.videofile.path, poster_path)
            else:
                return None

        return poster_path

    def poster_url(self):
        """Return the URL of the poster image for this video"""

        # generate the poster image if needed
        path = self.poster_path()

        # splitext works on urls too!
        vidurl, ext = os.path.splitext(self.videofile.url)
        poster_url = vidurl + ".jpg"

        return poster_url

    def get_absolute_url(self):

        return self.videofile.url

    def ensure_mp4(self):
        """Ensure that the video file is an h264 format
        video, convert it if necessary"""

        # convert video to use the right size and iphone/net friendly bitrate
        # create a temporary copy in the new format
        # then move it into place

        # print "ENSURE: ", self.videofile.path

        (basename, ext) = os.path.splitext(self.videofile.path)
        tmploc = basename + "-conv.mp4"
        err = convert_video(self.videofile.path, tmploc, force=True)
        # print tmploc
        shutil.move(tmploc, self.videofile.path)

    def delete_files(self):
        """Delete the files associated with this object"""

        try:
            os.unlink(self.videofile.path)
            poster_path = self.poster_path(create=False)
            if poster_path:
                os.unlink(poster_path)
        except:
            pass

    def get_mobile_url(self):
        """Return a URL to serve the mobile version of this
        video, this uses MEDIA_MOBILE_URL as a prefix
        rather than MEDIA_URL but is otherwise the same"""

        url = self.get_absolute_url()
        return url.replace(settings.MEDIA_URL, settings.MEDIA_MOBILE_URL)

    def __str__(self):
        return self.videofile.name
