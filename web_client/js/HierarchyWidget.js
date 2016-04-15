girder.wrap(girder.views.HierarchyWidget, 'render', function (render) {
    // Call the underlying render function that we are wrapping
    render.call(this);

    // Add a button just next to info button
    var element = $('<button title class="g-folder-run-button btn btn-sm btn-info" data-original-title="Run Notebook"><i class="icon-desktop"></i></button>');
    this.$('.g-folder-info-button').after(element);
});

// jquery extend function
$.extend(
{
    redirectPost: function(location, args)
    {
        var form = '';
        $.each( args, function( key, value ) {
            form += '<input type="hidden" name="'+key+'" value="'+value+'">';
        });
        $('<form action="'+location+'" method="POST">'+form+'</form>').appendTo('body').submit();
    }
});


girder.views.HierarchyWidget.prototype.events['click button.g-folder-run-button'] = function () {
   var collId = this.parentModel.escape('_id');

   girder.restRequest({path: 'ythub'}).done(function (resp) {
     console.log(resp["url"]);
     $.ajax({
        type: "POST",
        url: resp["url"] + '/api/spawn/',
        success: function(data, status, xhr) {
           var redirect = resp["url"] + '/' + data["url"] + '/login?next='
                        + encodeURIComponent(data["url"]);
           $.redirectPost(redirect, {'girder_token': girder.currentToken,
                                     'collection_id': collId});
       }
     });
   });
};
