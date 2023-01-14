from django.core.paginator import Paginator

from yatube.settings import POSTS_NUMBER_PER_PAGE


def pages(queryset, request):
    paginator = Paginator(queryset, POSTS_NUMBER_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return {
        'paginator': paginator,
        'page_number': page_number,
        'page_obj': page_obj,
    }
