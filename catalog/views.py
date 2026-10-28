from django.shortcuts import render

# Create your views here.

from .models import Book, Author, BookInstance, Genre

def index(request):
    """View function for home page of site."""

    # Generate counts of some of the main objects
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()

    # Available books (status = 'a')
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()

    # The 'all()' is implied by default.
    num_authors = Author.objects.count()
    num_visits = request.session.get('num_visits', 0)
    num_visits += 1
    request.session['num_visits'] = num_visits

    #Challenge 5.2
    num_genres = Genre.objects.filter(name__icontains='fict').count()
    num_books_with_word = Book.objects.filter(title__icontains='pizza').count()

    context = {
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_visits': num_visits,
        'num_genres': num_genres, 
        'num_books_with_word': num_books_with_word,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)

from django.views import generic

class BookListView(generic.ListView):
    model = Book
    paginate_by = 4

class BookDetailView(generic.DetailView):
    model = Book

class AuthorListView(generic.ListView):
    model = Author
    paginate_by = 4

class AuthorDetailView(generic.DetailView):
    model = Author


from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin


class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
    """Lists books on loan to the current user, soonest due first."""
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return (BookInstance.objects
                .filter(borrower=self.request.user)
                .filter(status__exact='o')
                .order_by('due_back'))


class LoanedBooksAllListView(PermissionRequiredMixin, generic.ListView):
    """Lists all books on loan. Only for users with can_mark_returned."""
    model = BookInstance
    permission_required = 'catalog.can_mark_returned'
    template_name = 'catalog/bookinstance_list_borrowed_all.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(status__exact='o').order_by('due_back')


# ---- Part 9: forms ----

import datetime

from django.contrib.auth.decorators import login_required, permission_required
from django.forms import inlineformset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from catalog.forms import RenewBookForm
from .models import BookAuthor


@login_required
@permission_required('catalog.can_mark_returned', raise_exception=True)
def renew_book_librarian(request, pk):
    """View function for renewing a specific BookInstance by librarian."""
    book_instance = get_object_or_404(BookInstance, pk=pk)

    # If this is a POST request then process the Form data
    if request.method == 'POST':
        # Create a form instance and populate it with data from the request (binding):
        form = RenewBookForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            book_instance.due_back = form.cleaned_data['renewal_date']
            book_instance.save()
            return HttpResponseRedirect(reverse('all-borrowed'))

    # If this is a GET (or any other method) create the default form.
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date})

    context = {
        'form': form,
        'book_instance': book_instance,
    }

    return render(request, 'catalog/book_renew_librarian.html', context)


class AuthorCreate(PermissionRequiredMixin, CreateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']
    permission_required = 'catalog.add_author'


class AuthorUpdate(PermissionRequiredMixin, UpdateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']
    permission_required = 'catalog.change_author'


class AuthorDelete(PermissionRequiredMixin, DeleteView):
    model = Author
    success_url = reverse_lazy('authors')
    permission_required = 'catalog.delete_author'

    def form_valid(self, form):
        # BookAuthor uses CASCADE, so refuse here rather than silently
        # removing the author from their books.
        if self.object.books.exists():
            return HttpResponseRedirect(reverse('author-delete', kwargs={'pk': self.object.pk}))
        try:
            self.object.delete()
            return HttpResponseRedirect(self.success_url)
        except Exception:
            return HttpResponseRedirect(reverse('author-delete', kwargs={'pk': self.object.pk}))


# ---- Challenge: Book create / update / delete ----

BookAuthorFormSet = inlineformset_factory(
    Book, BookAuthor, fields=['author', 'author_order'], extra=2)


class BookAuthorFormSetMixin:
    """Adds an inline formset of BookAuthor rows to a Book create/update view."""
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.method == 'POST':
            context['author_formset'] = BookAuthorFormSet(self.request.POST, instance=self.object)
        else:
            context['author_formset'] = BookAuthorFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        author_formset = BookAuthorFormSet(self.request.POST, instance=form.instance)
        if not author_formset.is_valid():
            return self.form_invalid(form)
        self.object = form.save()
        author_formset.instance = self.object
        author_formset.save()
        return HttpResponseRedirect(self.get_success_url())


class BookCreate(PermissionRequiredMixin, BookAuthorFormSetMixin, CreateView):
    model = Book
    fields = ['title', 'summary', 'isbn', 'genre', 'language']
    permission_required = 'catalog.add_book'


class BookUpdate(PermissionRequiredMixin, BookAuthorFormSetMixin, UpdateView):
    model = Book
    fields = ['title', 'summary', 'isbn', 'genre', 'language']
    permission_required = 'catalog.change_book'


class BookDelete(PermissionRequiredMixin, DeleteView):
    model = Book
    success_url = reverse_lazy('books')
    permission_required = 'catalog.delete_book'

    def form_valid(self, form):
        try:
            self.object.delete()
            return HttpResponseRedirect(self.success_url)
        except Exception:
            # BookInstance.book is RESTRICT, so a book with copies can't be deleted.
            return HttpResponseRedirect(reverse('book-delete', kwargs={'pk': self.object.pk}))
