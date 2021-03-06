import OpenGL.GL as ogl
import numpy
from PIL import Image


class RenderException(Exception):
    pass


class VertexState:
    """
    Maintains a draw state.
    VertexArray in opengl.
    Some assumptions are made about rendering here.
    Such as triangle use, uint for index element type.
    """

    def __init__(self) -> None:
        self.vao = ogl.glGenVertexArrays(1)

    def __enter__(self) -> None:
        self.bind()

    def __exit__(self, type, value, traceback) -> None:
        self.unbind()

    def bind(self) -> None:
        ogl.glBindVertexArray(self.vao)

    def unbind(self) -> None:
        ogl.glBindVertexArray(0)

    def draw_array(self, length: int) -> None:
        ogl.glDrawArrays(ogl.GL_TRIANGLES, 0, length)

    def draw_indexed_elements(self, length: int) -> None:
        ogl.glDrawElements(ogl.GL_TRIANGLES, length, ogl.GL_UNSIGNED_INT, None)

    def draw_instanced(self, length: int, instances: int) -> None:
        ogl.glDrawArraysInstanced(ogl.GL_TRIANGLES, 0, length, instances)

    def draw_instanced_indexed_elements(self, length: int, instances: int) -> None:
        ogl.glDrawElementsInstanced(
            ogl.GL_TRIANGLES, length, ogl.GL_UNSIGNED_INT, None, instances
        )


class VertexBuffer:
    """
    Respresents a buffer of data
    Probably should be run within a VertexState with block
    Using this class may fuck with openGL state not leaving it how it found it.
    """

    def __init__(
        self, data: list, program, name: str, stepping=3, instanced=False
    ) -> None:
        self.vbo = ogl.glGenBuffers(1)
        self.data = numpy.array(data, dtype="float32")
        self.name = name
        self.program = program
        self.instanced = instanced
        self.stepping = stepping
        self._buffer_data()

    def bind(self) -> None:
        ogl.glBindBuffer(ogl.GL_ARRAY_BUFFER, self.vbo)

    def unbind(self) -> None:
        ogl.glBindBuffer(ogl.GL_ARRAY_BUFFER, 0)

    def _buffer_data(self) -> None:
        self.bind()
        ogl.glBufferData(
            ogl.GL_ARRAY_BUFFER, len(self.data) * 4, self.data, ogl.GL_STATIC_DRAW
        )

        self.program.use()
        self.program.set_attribute(self.name, self.stepping)

        # If instanced this attribute is split between verticie instances.
        if self.instanced:
            ogl.glVertexAttribDivisor(self.program.get_attribute(self.name), 1)
        # self.unbind()


class IndexBuffer:
    """
    Index into a VBO.
    You generally have to create this straight after a VBO while it is still bound().
    """

    def __init__(self, data: list, program, name: str, stepping=3) -> None:
        self.vbo = ogl.glGenBuffers(1)
        self.data = numpy.array(data, dtype="uint32")  # This type matters
        self.name = name
        self.program = program
        self.stepping = stepping
        self._buffer_data()

    def bind(self) -> None:
        ogl.glBindBuffer(ogl.GL_ELEMENT_ARRAY_BUFFER, self.vbo)

    def unbind(self) -> None:
        ogl.glBindBuffer(ogl.GL_ELEMENT_ARRAY_BUFFER, 0)

    def _buffer_data(self) -> None:
        self.bind()
        ogl.glBufferData(
            ogl.GL_ELEMENT_ARRAY_BUFFER,
            len(self.data) * 4,
            self.data,
            ogl.GL_STATIC_DRAW,
        )

        self.program.use()
        self.program.set_attribute(self.name, self.stepping)
        # We dont unbind a GL_ELEMENT_ARRAY_BUFFER within the context of a vao
        # self.unbind()


class FrameBuffer:
    """
    Creates a framebuffer which when in context draw calls will render too.
    Stores the results in a texture which can be used.. as a texture.
    """

    def __init__(self, width, height) -> None:
        self.fbo = ogl.glGenFramebuffers(1)
        self.bind()

        #  TODO: Depth buffer for 3d support.
        self.texture = Texture(width, height, None)

        ogl.glFramebufferTexture2D(
            ogl.GL_FRAMEBUFFER,
            ogl.GL_COLOR_ATTACHMENT0,
            ogl.GL_TEXTURE_2D,
            self.texture.tbo,
            0,
        )

        self.unbind()

    def __enter__(self) -> None:
        self.bind()

    def __exit__(self, type, value, traceback) -> None:
        self.unbind()

    def bind_texture(self) -> None:
        self.texture.bind()

    def bind(self) -> None:
        ogl.glBindFramebuffer(ogl.GL_FRAMEBUFFER, self.fbo)

    def unbind(self) -> None:
        ogl.glBindFramebuffer(ogl.GL_FRAMEBUFFER, 0)

    def delete(self) -> None:
        ogl.glDeleteFramebuffers(1, self.fbo)


class Texture:
    """
    Images should be a power of 2.
    """

    def __init__(self, width, height, data, type=ogl.GL_TEXTURE_2D):
        self.tbo = ogl.glGenTextures(1)
        self.width = width
        self.height = height
        self.data = data
        self.type = type

        if type == ogl.GL_TEXTURE_2D:
            self._create_texture()
        elif type == ogl.GL_TEXTURE_CUBE_MAP:
            self._create_cubemap_texture()

    @staticmethod
    def image_from_file(file_path):
        image = Image.open(file_path)
        data = numpy.array(list(image.getdata()), numpy.uint8)
        return Texture(image.size[0], image.size[1], data)

    def bind(self) -> None:
        ogl.glBindTexture(self.type, self.tbo)

    def unbind(self) -> None:
        ogl.glBindTexture(self.type, 0)

    def _create_texture(self) -> None:
        self.bind()
        ogl.glPixelStorei(ogl.GL_UNPACK_ALIGNMENT, 4)
        ogl.glTexParameteri(ogl.GL_TEXTURE_2D, ogl.GL_TEXTURE_WRAP_S, ogl.GL_REPEAT)
        ogl.glTexParameteri(ogl.GL_TEXTURE_2D, ogl.GL_TEXTURE_WRAP_T, ogl.GL_REPEAT)
        ogl.glTexParameteri(ogl.GL_TEXTURE_2D, ogl.GL_TEXTURE_MIN_FILTER, ogl.GL_LINEAR)
        ogl.glTexParameteri(ogl.GL_TEXTURE_2D, ogl.GL_TEXTURE_MAG_FILTER, ogl.GL_LINEAR)
        ogl.glTexImage2D(
            ogl.GL_TEXTURE_2D,
            0,
            ogl.GL_RGB,
            self.width,
            self.height,
            0,
            ogl.GL_RGB,
            ogl.GL_UNSIGNED_BYTE,
            self.data,
        )
        ogl.glGenerateMipmap(ogl.GL_TEXTURE_2D)
        self.unbind()

    def _create_cubemap_texture(self) -> None:
        self.bind()
        ogl.glTexParameteri(
            ogl.GL_TEXTURE_CUBE_MAP, ogl.GL_TEXTURE_MAG_FILTER, ogl.GL_LINEAR
        )
        ogl.glTexParameteri(
            ogl.GL_TEXTURE_CUBE_MAP, ogl.GL_TEXTURE_MIN_FILTER, ogl.GL_LINEAR
        )
        ogl.glTexParameteri(
            ogl.GL_TEXTURE_CUBE_MAP, ogl.GL_TEXTURE_WRAP_S, ogl.GL_CLAMP_TO_EDGE
        )
        ogl.glTexParameteri(
            ogl.GL_TEXTURE_CUBE_MAP, ogl.GL_TEXTURE_WRAP_T, ogl.GL_CLAMP_TO_EDGE
        )
        ogl.glTexParameteri(
            ogl.GL_TEXTURE_CUBE_MAP, ogl.GL_TEXTURE_WRAP_R, ogl.GL_CLAMP_TO_EDGE
        )
        for n in range(0, 6):
            ogl.glTexImage2D(
                ogl.GL_TEXTURE_CUBE_MAP_POSITIVE_X + n,
                0,
                ogl.GL_RGB,
                self.width,
                self.height,
                0,
                ogl.GL_RGB,
                ogl.GL_UNSIGNED_BYTE,
                self.data,
            )
        ogl.glGenerateMipmap(ogl.GL_TEXTURE_2D)
        self.unbind()
