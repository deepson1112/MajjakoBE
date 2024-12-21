from functools import reduce
from django.db.models import Q, Case, When, Value, IntegerField
from rest_framework.filters import SearchFilter
import operator


class PrioritizedSearchFilter(SearchFilter):
    def filter_queryset(self, request, queryset, view):
        """
        Perform priority-based filtering, ensuring matches in fields like `name`
        have the highest priority, followed by others.
        """
        search_terms = self.get_search_terms(request)  # Extract search terms
        search_fields = getattr(view, "search_fields", None)  # Extract search fields

        if not search_fields or not search_terms:
            return queryset  # Return the original queryset if nothing to search.

        # Initialize querysets for all prioritized results
        prioritized_queryset = []

        # Iterate over search fields (in priority order)
        for priority, search_field in enumerate(search_fields):
            for search_term in search_terms:
                # Create a filtered queryset for this search field and search term
                filtered_queryset = (
                    queryset.filter(Q(**{f"{search_field}__icontains": search_term}))
                    .annotate(
                        priority=Value(
                            len(search_fields) - priority,  # Higher priority for fields earlier in the list
                            output_field=IntegerField(),
                        )
                    )
                )
                prioritized_queryset.append(filtered_queryset)

        # Combine all prioritized querysets using OR logic
        combined_queryset = reduce(operator.or_, prioritized_queryset)

        # Order by the annotated priority (higher priority first)
        final_queryset = combined_queryset.order_by("-priority")

        # Ensure distinct results (to avoid duplicates in many-to-many relationships)
        if self.must_call_distinct(final_queryset, search_fields):
            final_queryset = final_queryset.distinct()

        return final_queryset
