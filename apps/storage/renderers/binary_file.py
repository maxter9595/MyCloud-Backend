from rest_framework.renderers import BaseRenderer


class BinaryFileRenderer(BaseRenderer):
    media_type = 'application/octet-stream'
    format = 'binary'
    charset = None
    render_style = 'binary'

    def render(self, data, media_type=None, renderer_context=None):
        """
        Renders binary data into a format that can be
        transmitted over HTTP.  The data is expected
        to be a bytes object or a string containing
        the file contents.

        :param data: The binary data to be rendered.
        :param media_type: The media type of the output.
        :param renderer_context: The renderer context
        containing the response object.
        """
        return data
