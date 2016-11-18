import re
from girder.models.model_base import \
    AccessControlledModel, ValidationException
from girder.constants import AccessType


class Frontend(AccessControlledModel):

    def initialize(self):
        self.name = 'frontend'
        self.exposeFields(level=AccessType.READ,
                          fields={'_id', 'imageName'})

    def validate(self, frontend):
        if not re.match('(?:[a-z]+/)?([a-z]+)(?::[0-9]+)?',
                        frontend['imageName']):
            raise ValidationException(
                'Invalid image name: %s.' % frontend['imageName'],
                field='imageName')
        return frontend

    def createFrontend(self, imageName, save=True):
        frontend = {
            'imageName': imageName
        }
        if save:
            frontend = self.save(frontend)
        return frontend
