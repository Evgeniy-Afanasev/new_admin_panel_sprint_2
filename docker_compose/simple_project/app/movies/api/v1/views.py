from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Q, Value
from django.http import JsonResponse
from django.views.generic.detail import BaseDetailView
from django.views.generic.list import BaseListView
from django.db.models.functions import Coalesce

from movies.models import FilmWork, Roles


class MoviesApiMixin:
    model = FilmWork
    http_method_names = ['get']

    @staticmethod
    def get_person_array_agg(role: Roles):
        return ArrayAgg(
            'persons__full_name',
            filter=Q(personfilmwork__role__icontains=role),
            distinct=True
        )

    def get_queryset(self):
        qs = FilmWork.objects.values(
            'genres', 'persons'
        ).values(
            'id',
            'title',
            'description',
            'creation_date',
            'rating', 'type'
        ).annotate(
            genres=ArrayAgg(
                'genres__name',
                distinct=True
            ),
            actors=Coalesce(MoviesApiMixin.get_person_array_agg(Roles.ACTOR), Value([])),
            directors=Coalesce(MoviesApiMixin.get_person_array_agg(Roles.DIRECTOR), Value([])),
            writers=Coalesce(MoviesApiMixin.get_person_array_agg(Roles.WRITER), Value([]))
        )
        return qs

    def render_to_response(self, context, **response_kwargs):
        return JsonResponse(context)


class MoviesListApi(MoviesApiMixin, BaseListView):

    def get_context_data(self, *, object_list=None, **kwargs):
        queryset = self.get_queryset()
        paginator, page, queryset, is_paginated = self.paginate_queryset(queryset, 50)
        prev_page = None
        next_page = None
        if page.has_previous():
            prev_page = page.previous_page_number()
        if page.has_next():
            next_page = page.next_page_number()
        return {
            "count": paginator.count,
            "total_pages": paginator.num_pages,
            "prev": prev_page,
            "next": next_page,
            "results": list(queryset)
        }


class MoviesDetailApi(MoviesApiMixin, BaseDetailView):

    def get_context_data(self, **kwargs):
        return self.object