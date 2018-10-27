from django.shortcuts import get_object_or_404, render  # https://docs.djangoproject.com/en/2.1/_modules/django/shortcuts/
from django.core.paginator import Paginator # https://docs.djangoproject.com/en/2.1/topics/pagination/
from django.conf import settings # https://docs.djangoproject.com/en/2.1/ref/settings/
from django.db.models import Count # https://docs.djangoproject.com/en/2.1/topics/db/aggregation/
from django.contrib.contenttypes.models import ContentType # https://docs.djangoproject.com/en/2.1/ref/contrib/contenttypes/

from .models import Blog, BlogType
from read_statistics.utils import read_statistics_once_read

# Create your views here.
def get_blog_list_common_data(request, blogs_all_list):
	'''处理拿到的博客数据，处理页码'''
	paginator = Paginator(blogs_all_list, settings.EACH_PAGE_BLOGS_NUMBER)
	page_num = request.GET.get('page', 1) # 获取url的页面参数（GET请求）
	page_of_blogs = paginator.get_page(page_num)
	current_page_num = page_of_blogs.number # 获取当前页面
	# 获取当前页码前后2页的页码范围
	page_range = list(range(max(current_page_num - 2, 1), current_page_num)) +\
	list(range(current_page_num, min(current_page_num+2, paginator.num_pages)+1))
	# 加上省略页码标记
	if page_range[0] - 1 >=2:
		page_range.insert(0, '...')
	if paginator.num_pages - page_range[-1] >= 2:
		page_range.append('...')

	# 加上首页和末页
	if page_range[0] != 1:
		page_range.insert(0,1)
	if page_range[-1] != paginator.num_pages:
		page_range.append(paginator.num_pages)

	# 获取日期归档对应的博客数量
	blog_dates = Blog.objects.dates('created_time', 'month', order='DESC')
	blog_dates_dict = {}
	for blog_date in blog_dates:
		blog_count = Blog.objects.filter(created_time__year=blog_date.year,
			created_time__month=blog_date.month).count() # 这里的__year和__month需要考察
		blog_dates_dict[blog_date] = blog_count

	context = {}
	context['blogs'] = page_of_blogs.object_list
	context['page_of_blogs'] = page_of_blogs
	context['page_range'] = page_range
	context['blog_types'] = BlogType.objects.annotate(blog_count=Count('blog')) # annotate需要考察
	context['blog_dates'] = blog_dates_dict
	return context

def blog_list(request):
	'''拿到所有的博客列表'''
	blogs_all_list = Blog.objects.all()
	context = get_blog_list_common_data(request, blogs_all_list)
	return render(request, 'blog/blog_list.html', context)

def blogs_with_type(request, blog_type_pk):
	'''拿到某种类型的博客列表'''
	blog_type = get_object_or_404(BlogType, pk=blog_type_pk)
	blogs_all_list = Blog.objects.filter(blog_type=blog_type)
	context = get_blog_list_common_data(request,blogs_all_list)
	context['blog_type'] = blog_type
	return render(request, 'blog/blogs_with_date.html', context)

def blog_with_date(request, year, month):
	'''拿到某个日期的博客列表'''
	blogs_all_list = Blog.objects.filter(created_time__year=year, created_time__month=month) # 横线写法
	context = get_blog_list_common_data(request, blog_all_list)
	context['blogs_with_date'] = '%s年%s月'%(year, month)
	return render(request, 'blog/blogs_with_date.html', context)

def blog_detail(request, blog_pk):
	'''显示详细博客内容'''
	blog = get_object_or_404(Blog, pk=blog_pk)
	read_cookie_key = read_statistics_once_read(request, blog)

	context = {}
	context['previous_blog'] = Blog.objects.filter(created_time__gt=blog.created_time).last()
	context['next_blog'] = Blog.objects.filter(created_time__lt=blog.created_time).first()
	context['blog'] = blog
	response = render(request, 'blog/blog_detail.html', context)
	response.set_cookie(read_cookie_key, 'true') # set_cookie写法
	return response