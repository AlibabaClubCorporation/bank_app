from django.db.models import Model
from rest_framework.views import APIView
from rest_framework.response import Response

from bank_controller.services.general_service import *



class ClearHistoryMixinAPIView( APIView ):
    """
        View for clear history
    """

    # Required to specify. Required to define a model with the "is_ignore" field for the PUT method to work
    model = None

    # The "PUT" method of this mixin class requires the "model" class attribute to be specified.
    # Redefining the "as_view" class method allows you to check for the presence of this "model" attribute,
    # and allows you to raise an error at the stage of determining the routers "urls.py" where the "as_view" ...
    # ... method was called on the child view.

    # This can happen after the command "runserver" for "manage.py" in the console,
    # when the handler reaches the urls.py file where the child view was specified,
    # which had "as_view" called.
    @classmethod
    def as_view(cls, **initkwargs):

        # If the "Model" attribute of the class is missing, it causes an attribute error.
        if not cls.model:
            error_message = 'For the view inherited from ClearHistoryMixinView to work, you must specify a value for the "model" attribute'
            raise AttributeError( error_message )

        # If the value passed to the 'model' class attribute is not a Django model - throws an attribute error
        try:
            assert issubclass( cls.model, Model )
        except Exception:
            error_message = 'The specified value for the "model" class attribute is not a Django model. You need to specify a Django model with a "is_ignore" field for the "model" class attribute'
            raise AttributeError( error_message )

        # If the specified value in the "model" class attribute does not have the ...
        # ... "is_ignor" attribute, causes an attribute error
        try:
            cls.model.is_ignore
        except AttributeError:
            error_message = 'A value was specified in the "model" class attribute that did not have the "is_ignore" attribute. You must specify a Django model object with an "is_ignore" field to work correctly'
            raise AttributeError( error_message )


        return super().as_view( **initkwargs )

    @classmethod
    def put( cls, request ):
        """
            Validates the data, then tries to set the "is_ignore" field to "True" for the specified Purchase records,
            or for all records if the "id_list" parameter was not specified in the request body.
        """

        id_list = request.data.get( 'id_list' )

        if not id_list:
            set_ignore_status_for_queryset( True, cls.model.objects.all() )
        else:
            validation_result = id_list_validate( id_list )
            
            if not validation_result[0]:
                return Response( data = validation_result[1], status = 400 )
                
            queryset = cls.model.objects.filter( pk__in = id_list )
            set_ignore_status_for_queryset( True, queryset = queryset )
        
        return Response( status = 200 )