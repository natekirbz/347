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
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return (BookInstance.objects
                .filter(borrower=self.request.user)
                .filter(status__exact='o')
                .order_by('due_back'))


class LoanedBooksAllListView(PermissionRequiredMixin, generic.ListView):
    model = BookInstance
    permission_required = 'catalog.can_mark_returned'
    template_name = 'catalog/bookinstance_list_borrowed_all.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(status__exact='o').order_by('due_back')


import datetime

from django.contrib.auth.decorators import login_required, permission_required
from django.forms import ModelForm, inlineformset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from catalog.forms import RenewBookForm
from .models import BookAuthor


@login_required
@permission_required('catalog.can_mark_returned', raise_exception=True)
def renew_book_librarian(request, pk):
    book_instance = get_object_or_404(BookInstance, pk=pk)

    if request.method == 'POST':
        form = RenewBookForm(request.POST)

        if form.is_valid():
            book_instance.due_back = form.cleaned_data['renewal_date']
            book_instance.save()
            return HttpResponseRedirect(reverse('all-borrowed'))

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
        if self.object.books.exists():
            return HttpResponseRedirect(reverse('author-delete', kwargs={'pk': self.object.pk}))
        try:
            self.object.delete()
            return HttpResponseRedirect(self.success_url)
        except Exception:
            return HttpResponseRedirect(reverse('author-delete', kwargs={'pk': self.object.pk}))


class BookAuthorForm(ModelForm):
    class Meta:
        model = BookAuthor
        fields = ['author', 'author_order']

    def has_changed(self):
        if not self.data.get(self.add_prefix('author')) and not self.instance.pk:
            return False
        return super().has_changed()


BookAuthorFormSet = inlineformset_factory(
    Book, BookAuthor, form=BookAuthorForm, extra=2)


class BookAuthorFormSetMixin:
    def get_formset(self, instance):
        if self.request.method == 'POST' and self._has_formset_data():
            return BookAuthorFormSet(self.request.POST, instance=instance)
        return BookAuthorFormSet(instance=instance)

    def _has_formset_data(self):
        return f'{BookAuthorFormSet.get_default_prefix()}-TOTAL_FORMS' in self.request.POST

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault('author_formset', self.get_formset(self.object))
        return context

    def form_valid(self, form):
        if not self._has_formset_data():
            self.object = form.save()
            return HttpResponseRedirect(self.get_success_url())
        author_formset = BookAuthorFormSet(self.request.POST, instance=form.instance)
        if not author_formset.is_valid():
            return self.render_to_response(
                self.get_context_data(form=form, author_formset=author_formset))
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
            return HttpResponseRedirect(reverse('book-delete', kwargs={'pk': self.object.pk}))
