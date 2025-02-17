"""Primitives, conforming to the glTF 2.0 standards as specified in
https://github.com/KhronosGroup/glTF/tree/master/specification/2.0#reference-primitive

Author: Matthew Matl
"""
import numpy as np

from OpenGL.GL import *

from .material import Material, MetallicRoughnessMaterial
from .constants import FLOAT_SZ, UINT_SZ, BufFlags, GLTF
from .utils import format_color_array
from .texture import Texture
from .sampler import Sampler

class Primitive(object):
    """A primitive object which can be rendered.

    Parameters
    ----------
    positions : (n, 3) float
        XYZ vertex positions.
    normals : (n, 3) float
        Normalized XYZ vertex normals.
    tangents : (n, 4) float
        XYZW vertex tangents where the w component is a sign value
        (either +1 or -1) indicating the handedness of the tangent basis.
    texcoord_0 : (n, 2) float
        The first set of UV texture coordinates.
    texcoord_1 : (n, 2) float
        The second set of UV texture coordinates.
    color_0 : (n, 4) float
        RGBA vertex colors.
    joints_0 : (n, 4) float
        Joint information.
    weights_0 : (n, 4) float
        Weight information for morphing.
    indices : (m, 3) int
        Face indices for triangle meshes or fans.
    material : :class:`Material`
        The material to apply to this primitive when rendering.
    mode : int
        The type of primitives to render, one of the following:

        - ``0``: POINTS
        - ``1``: LINES
        - ``2``: LINE_LOOP
        - ``3``: LINE_STRIP
        - ``4``: TRIANGLES
        - ``5``: TRIANGLES_STRIP
        - ``6``: TRIANGLES_FAN
    targets : (k,) int
        Morph target indices.
    poses : (x,4,4), float
        Array of 4x4 transformation matrices for instancing this object.
    """

    def __init__(self,
                 positions,
                 normals=None,
                 tangents=None,
                 texcoord_0=None,
                 texcoord_1=None,
                 color_0=None,
                 joints_0=None,
                 weights_0=None,
                 blendshapes_0=None,
                 coes_0=None,
                 indices=None,
                 material=None,
                 mode=None,
                 targets=None,
                 poses=None, ):

        if mode is None:
            mode = GLTF.TRIANGLES

        self.positions = positions
        self.normals = normals
        self.tangents = tangents
        self.texcoord_0 = texcoord_0
        self.texcoord_1 = texcoord_1
        self.color_0 = color_0
        self.joints_0 = joints_0
        self.weights_0 = weights_0
        self.blendshapes_0 = blendshapes_0
        self.coes_0 = coes_0
        self.indices = indices
        self.material = material
        self.mode = mode
        self.targets = targets
        self.poses = poses
        

        self._bounds = None
        self._vaid = None
        self._buffers = []
        self._is_transparent = None
        self._buf_flags = None
        self._blendshape_texture = None
        self._blendshape_texture_id = None

    @property
    def positions(self):
        """(n,3) float : XYZ vertex positions.
        """
        return self._positions

    @positions.setter
    def positions(self, value):
        value = np.asanyarray(value, dtype=np.float32)
        self._positions = np.ascontiguousarray(value)
        self._bounds = None

    @property
    def normals(self):
        """(n,3) float : Normalized XYZ vertex normals.
        """
        return self._normals

    @normals.setter
    def normals(self, value):
        if value is not None:
            value = np.asanyarray(value, dtype=np.float32)
            value = np.ascontiguousarray(value)
            if value.shape != self.positions.shape:
                raise ValueError('Incorrect normals shape')
        self._normals = value

    @property
    def tangents(self):
        """(n,4) float : XYZW vertex tangents.
        """
        return self._tangents

    @tangents.setter
    def tangents(self, value):
        if value is not None:
            value = np.asanyarray(value, dtype=np.float32)
            value = np.ascontiguousarray(value)
            if value.shape != (self.positions.shape[0], 4):
                raise ValueError('Incorrect tangent shape')
        self._tangents = value

    @property
    def texcoord_0(self):
        """(n,2) float : The first set of UV texture coordinates.
        """
        return self._texcoord_0

    @texcoord_0.setter
    def texcoord_0(self, value):
        if value is not None:
            value = np.asanyarray(value, dtype=np.float32)
            value = np.ascontiguousarray(value)
            if (value.ndim != 2 or value.shape[0] != self.positions.shape[0] or
                    value.shape[1] < 2):
                raise ValueError('Incorrect texture coordinate shape')
            if value.shape[1] > 2:
                value = value[:,:2]
        self._texcoord_0 = value

    @property
    def texcoord_1(self):
        """(n,2) float : The second set of UV texture coordinates.
        """
        return self._texcoord_1

    @texcoord_1.setter
    def texcoord_1(self, value):
        if value is not None:
            value = np.asanyarray(value, dtype=np.float32)
            value = np.ascontiguousarray(value)
            if (value.ndim != 2 or value.shape[0] != self.positions.shape[0] or
                    value.shape[1] != 2):
                raise ValueError('Incorrect texture coordinate shape')
        self._texcoord_1 = value

    @property
    def color_0(self):
        """(n,4) float : RGBA vertex colors.
        """
        return self._color_0

    @color_0.setter
    def color_0(self, value):
        if value is not None:
            value = np.ascontiguousarray(
                format_color_array(value, shape=(len(self.positions), 4))
            )
        self._is_transparent = None
        self._color_0 = value

    @property
    def joints_0(self):
        """(n,4) float : Joint information.
        """
        return self._joints_0

    @joints_0.setter
    def joints_0(self, value):
        self._joints_0 = value

    @property
    def weights_0(self):
        """(n,4) float : Weight information for morphing.
        """
        return self._weights_0

    @weights_0.setter
    def weights_0(self, value):
        self._weights_0 = value

    @property
    def blendshapes_0(self):
        """(n,m,3) float : Per vertex linear blendshapes.
        """
        return self._blendshapes

    @blendshapes_0.setter
    def blendshapes_0(self, value):
        if value is not None:
        
            value = np.asanyarray(value, dtype=np.float32)
            # value = np.ascontiguousarray(value)
            assert value.ndim == 3, 'Blendshapes must be 3D but got {}D'.format(value.ndim)
            assert value.shape[0] == self.positions.shape[0], 'Blendshapes must have same number of vertices as positions'
            assert value.shape[2] == 3, 'Blendshapes must be in format [n, m, 3]' 
            
            self._blendshapes = value
            blendshapes_data = np.concatenate([value, np.ones([value.shape[0], value.shape[1], 1])], axis=2) # add alpha channel
            normalized = blendshapes_data/self.blendshape_abs_max / 2 + 0.5
            assert normalized.min() >= 0, normalized.min()
            assert normalized.max() <= 1, normalized.max()
            assert self.texcoord_1 is None, 'Cannot use blendshapes with texcoord_1'
            self.texcoord_1 = np.arange(value.shape[0]).reshape(-1,1).repeat(2, axis=1) / (value.shape[0]-1)

            self._blendshape_texture = Texture('blendshapes_texture', 
                    sampler=Sampler(
                        magFilter=GL_NEAREST,
                        minFilter=GL_NEAREST,
                        wrapS=GL_CLAMP_TO_EDGE,
                        wrapT=GL_CLAMP_TO_EDGE
                        ),
                    source=normalized, 
                    source_channels='RGBA',
                    )
            self._coes_0 = np.zeros(value.shape[1])
        self._blendshapes = value
    
    @property
    def blendshape_abs_max(self):
        if self._blendshapes is None:
            return 0
        return np.abs(self._blendshapes).max()
    
    @property
    def coes_0(self):
        """(n,4) float : Weight information for blendshape morphing."""
        return self._coes_0

    @coes_0.setter
    def coes_0(self, value):
        if value is not None:
            assert self.blendshapes_0 is not None, 'Cannot set coes without blendshapes'
            assert len(value) == self.blendshapes_0.shape[1], 'Coes must have same number of blendshapes as blendshapes'
        self._coes_0 = value
        

    @property
    def n_blendshapes_0(self):
        if self.blendshapes_0 is not None:
            return self.blendshapes_0.shape[1]
        return 0

    @property
    def indices(self):
        """(m,3) int : Face indices for triangle meshes or fans.
        """
        return self._indices

    @indices.setter
    def indices(self, value):
        if value is not None:
            value = np.asanyarray(value, dtype=np.float32)
            value = np.ascontiguousarray(value)
        self._indices = value

    @property
    def material(self):
        """:class:`Material` : The material for this primitive.
        """
        return self._material

    @material.setter
    def material(self, value):
        # Create default material
        if value is None:
            value = MetallicRoughnessMaterial()
        else:
            if not isinstance(value, Material):
                raise TypeError('Object material must be of type Material')
        self._material = value

    @property
    def mode(self):
        """int : The type of primitive to render.
        """
        return self._mode

    @mode.setter
    def mode(self, value):
        value = int(value)
        if value < GLTF.POINTS or value > GLTF.TRIANGLE_FAN:
            raise ValueError('Invalid mode')
        self._mode = value

    @property
    def targets(self):
        """(k,) int : Morph target indices.
        """
        return self._targets

    @targets.setter
    def targets(self, value):
        self._targets = value

    @property
    def poses(self):
        """(x,4,4) float : Homogenous transforms for instancing this primitive.
        """
        return self._poses

    @poses.setter
    def poses(self, value):
        if value is not None:
            value = np.asanyarray(value, dtype=np.float32)
            value = np.ascontiguousarray(value)
            if value.ndim == 2:
                value = value[np.newaxis,:,:]
            if value.shape[1] != 4 or value.shape[2] != 4:
                raise ValueError('Pose matrices must be of shape (n,4,4), '
                                 'got {}'.format(value.shape))
        self._poses = value
        self._bounds = None

    @property
    def bounds(self):
        if self._bounds is None:
            self._bounds = self._compute_bounds()
        return self._bounds

    @property
    def centroid(self):
        """(3,) float : The centroid of the primitive's AABB.
        """
        return np.mean(self.bounds, axis=0)

    @property
    def extents(self):
        """(3,) float : The lengths of the axes of the primitive's AABB.
        """
        return np.diff(self.bounds, axis=0).reshape(-1)

    @property
    def scale(self):
        """(3,) float : The length of the diagonal of the primitive's AABB.
        """
        return np.linalg.norm(self.extents)

    @property
    def buf_flags(self):
        """int : The flags for the render buffer.
        """
        if self._buf_flags is None:
            self._buf_flags = self._compute_buf_flags()
        return self._buf_flags

    def delete(self):
        self._unbind()
        self._remove_from_context()

    @property
    def is_transparent(self):
        """bool : If True, the mesh is partially-transparent.
        """
        return self._compute_transparency()

    def _add_to_context(self):
        if self._vaid is not None:
            raise ValueError('Mesh is already bound to a context')

        # Generate and bind VAO
        self._vaid = glGenVertexArrays(1)
        glBindVertexArray(self._vaid)

        #######################################################################
        # Fill vertex buffer
        #######################################################################

        # Generate and bind vertex buffer
        vertexbuffer = glGenBuffers(1)
        self._buffers.append(vertexbuffer)
        glBindBuffer(GL_ARRAY_BUFFER, vertexbuffer)

        # positions
        vertex_data = self.positions
        attr_sizes = [3]

        # Normals
        if self.normals is not None:
            vertex_data = np.hstack((vertex_data, self.normals))
            attr_sizes.append(3)

        # Tangents
        if self.tangents is not None:
            vertex_data = np.hstack((vertex_data, self.tangents))
            attr_sizes.append(4)

        # Texture Coordinates
        if self.texcoord_0 is not None:
            vertex_data = np.hstack((vertex_data, self.texcoord_0))
            attr_sizes.append(2)
        if self.texcoord_1 is not None:
            vertex_data = np.hstack((vertex_data, self.texcoord_1))
            attr_sizes.append(2)

        # Color
        if self.color_0 is not None:
            vertex_data = np.hstack((vertex_data, self.color_0))
            attr_sizes.append(4)

        # Copy data to buffer
        vertex_data = np.ascontiguousarray(
            vertex_data.flatten().astype(np.float32)
        )
        glBufferData(
            GL_ARRAY_BUFFER, FLOAT_SZ * len(vertex_data),
            vertex_data, GL_STATIC_DRAW
        )
        
        
        total_sz = sum(attr_sizes)
        offset = 0
        for i, sz in enumerate(attr_sizes):
            glVertexAttribPointer(
                i, sz, GL_FLOAT, GL_FALSE, FLOAT_SZ * total_sz,
                ctypes.c_void_p(FLOAT_SZ * offset)
            )
            glEnableVertexAttribArray(i)
            offset += sz


        #######################################################################
        # Fill model matrix buffer
        #######################################################################

        if self.poses is not None:
            pose_data = np.ascontiguousarray(
                np.transpose(self.poses, [0,2,1]).flatten().astype(np.float32)
            )
        else:
            pose_data = np.ascontiguousarray(
                np.eye(4).flatten().astype(np.float32)
            )

        modelbuffer = glGenBuffers(1)
        self._buffers.append(modelbuffer)
        glBindBuffer(GL_ARRAY_BUFFER, modelbuffer)
        glBufferData(
            GL_ARRAY_BUFFER, FLOAT_SZ * len(pose_data),
            pose_data, GL_DYNAMIC_DRAW
        )

        for i in range(0, 4):
            idx = i + len(attr_sizes)
            glEnableVertexAttribArray(idx)
            glVertexAttribPointer(
                idx, 4, GL_FLOAT, GL_FALSE, FLOAT_SZ * 4 * 4,
                ctypes.c_void_p(4 * FLOAT_SZ * i)
            )
            glVertexAttribDivisor(idx, 1)
            
        #######################################################################
        # Fill element buffer
        #######################################################################
        if self.indices is not None:
            elementbuffer = glGenBuffers(1)
            self._buffers.append(elementbuffer)
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, elementbuffer)
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, UINT_SZ * self.indices.size,
                         self.indices.flatten().astype(np.uint32),
                         GL_STATIC_DRAW)

        glBindVertexArray(0)
        
        #######################################################################
        # Fill Blendshapes buffer
        #######################################################################

        if self.blendshapes_0 is not None:
            # self._blendshape_texture_id = glGenTextures(1)
            # glBindTexture(GL_TEXTURE_2D, self._blendshape_texture_id)
            # blendshapes_data = np.concatenate([self.blendshapes_0, np.ones([self.blendshapes_0.shape[0], self.blendshapes_0.shape[1], 1])], axis=2)
            # blendshapes_data = np.ascontiguousarray(np.flip(blendshapes_data, axis=0).flatten().astype(np.float32))
            # normalized_blendshapes_data = blendshapes_data / self.blendshape_abs_max / 2 + 0.5
            
            
            
            # # Set texture parameters
            # glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            # glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
            # glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            # glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

            # width = self.blendshapes_0.shape[1] # n blendshapes
            # height = self.blendshapes_0.shape[0] # n vertex
            # print(f'Blendshape Texture: {width}, {height}')
            # assert normalized_blendshapes_data.min() >= 0, normalized_blendshapes_data.min()
            # assert normalized_blendshapes_data.max() <= 1, normalized_blendshapes_data.max()
            
            
            # glTexImage2D(
            #     GL_TEXTURE_2D, 0, GL_RGBA32F, width, height, 0, GL_RGBA,
            #     GL_FLOAT, normalized_blendshapes_data
            # )
            self._blendshape_texture._add_to_context()


    def _remove_from_context(self):
        if self._vaid is not None:
            glDeleteVertexArrays(1, [self._vaid])
            glDeleteBuffers(len(self._buffers), self._buffers)
            self._vaid = None
            self._buffers = []
            if self.blendshapes_0 is not None:
                self._blendshape_texture._remove_from_context()
                # glDeleteTextures([self._blendshape_texture_id])
                # self._blendshape_texture_id = None
            
            

    def _in_context(self):
        return self._vaid is not None

    def _bind(self):
        if self._vaid is None:
            raise ValueError('Cannot bind a Mesh that has not been added '
                             'to a context')
        glBindVertexArray(self._vaid)
        if self._blendshape_texture_id is not None:
            self._blendshape_texture._bind()
            # glBindTexture(GL_TEXTURE_2D, self._blendshape_texture_id)

    def _unbind(self):
        glBindVertexArray(0)
        if self._blendshape_texture_id is not None:
            # glBindTexture(GL_TEXTURE_2D, 0)
            self._blendshape_texture._unbind()

    def _compute_bounds(self):
        """Compute the bounds of this object.
        """
        # Compute bounds of this object
        bounds = np.array([np.min(self.positions, axis=0),
                           np.max(self.positions, axis=0)])

        # If instanced, compute translations for approximate bounds
        if self.poses is not None:
            bounds += np.array([np.min(self.poses[:,:3,3], axis=0),
                                np.max(self.poses[:,:3,3], axis=0)])
        return bounds

    def _compute_transparency(self):
        """Compute whether or not this object is transparent.
        """
        if self.material.is_transparent:
            return True
        if self._is_transparent is None:
            self._is_transparent = False
            if self.color_0 is not None:
                if np.any(self._color_0[:,3] != 1.0):
                    self._is_transparent = True
        return self._is_transparent

    def _compute_buf_flags(self):
        buf_flags = BufFlags.POSITION

        if self.normals is not None:
            buf_flags |= BufFlags.NORMAL
        if self.tangents is not None:
            buf_flags |= BufFlags.TANGENT
        if self.texcoord_0 is not None:
            buf_flags |= BufFlags.TEXCOORD_0
        if self.texcoord_1 is not None:
            buf_flags |= BufFlags.TEXCOORD_1
        if self.color_0 is not None:
            buf_flags |= BufFlags.COLOR_0
        if self.joints_0 is not None:
            buf_flags |= BufFlags.JOINTS_0
        if self.weights_0 is not None:
            buf_flags |= BufFlags.WEIGHTS_0
        if self.blendshapes_0 is not None:
            buf_flags |= BufFlags.BLENDSHAPES_0
        return buf_flags
