def family_group_context(request):
    """Context processor to add family group information to templates."""
    context = {}

    if hasattr(request, 'family_groups'):
        context['family_groups'] = request.family_groups

    if hasattr(request, 'current_family_group'):
        context['current_family_group'] = request.current_family_group

    return context