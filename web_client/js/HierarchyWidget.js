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
   var tmpnb = 'https://tmpnb.hub.yt';
   var collId = this.parentModel.escape('_id');
   $.ajax({
       type: "POST",
       url: tmpnb + '/api/spawn/',
       success: function(data, status, xhr) {
	   var redirect = tmpnb + '/' + data["url"] + '/login?next=' 
                        + encodeURIComponent(data["url"]);
           $.redirectPost(redirect, {'girder_token': girder.currentToken, 
                                     'collection_id': collId});
       }
   });
};
