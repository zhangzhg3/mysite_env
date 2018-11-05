from django.shortcuts import get_object_or_404, render
from django.core.paginator import Paginator
from django.conf import settings
from django.db.models import Count
from django.contrib.contenttypes.models import ContentType

from .models import Blog, BlogType
from read_statistics.utils import read_statistics_once_read
from mysite.forms import LoginForm


# Create your views here.  ####输出什么东西，一个是网页，一个是网页的内容；下一步是编辑网页排版

# each_page_blogs_number = 3

def get_blog_list_common_data(request,blogs_all_list):
    paginator = Paginator(blogs_all_list,settings.EACH_PAGE_BLOGS_NUMBER)   ###每10个进行分页
    page_num = request.GET.get('page',1)   ###get请求参数从request中获取，‘1’为默认获取第一页，获取url的页面参数（GET请求）/?page=1,不同于post请求/page/1
    # page_of_blogs = paginator.page(int(page_num))   ###前端输入的参数不可控，如果是a b c或空或超出页码的字符之类的用int转换就会出错，因此用下面那种方法代替
    page_of_blogs = paginator.get_page(page_num)
    current_range_num = page_of_blogs.number   ###获取当前页码
    page_range = list(range(max(current_range_num-2,1),current_range_num)) + list(range(current_range_num,min(current_range_num+2,paginator.num_pages)+1))
    # 加上省略页码标记
    if page_range[0] -1 >=2:
        page_range.insert(0,'...')
    if paginator.num_pages - page_range[-1] >= 2:
        page_range.append('...')
    # 加上首页和尾页
    if page_range[0] != 1:
        page_range.insert(0,1)
    if page_range[-1] != paginator.num_pages:
        page_range.append(paginator.num_pages)


    ### 获取博客分类的对应博客数量
    BlogType.objects.annotate(blog_count = Count('blog'))   #Count()里面传一个参数，该参数是关联对象的小写，如果明确点可以在modes.py写blog_type = models.ForeignKey(BlogType,on_delete=models.DO_NOTHING,related_name='blog';blog_count则相当于在BlogType中增加了一个字段)
    # BlogType.objects.annotate(blog_count = Count('blog')) = BlogType.objects.all().annotate(blog_count = Count('blog'))
    '''
    blog_types = BlogType.objects.all()
    blog_types_list = []
    for blog_type in blog_types:
        blog_type.blog_count = Blog.objects.filter(blog_type = blog_type).count()
        blog_types_list.append(blog_type)
    '''


    ### 获取日期归档对应的博客数量
    blog_dates = Blog.objects.dates('created_time','month',order='DESC')   ### 可以打开shell界面看下，这个是字典，不可以像blog_types_list那样append
    blog_dates_dict = {}
    for blog_date in blog_dates:
        blog_count = Blog.objects.filter(created_time__year = blog_date.year,
                            created_time__month = blog_date.month).count()
        blog_dates_dict[blog_date] = blog_count



    context = {}
    # context['blogs'] = Blog.objects.all()   ###获取全部列表
    context['blogs'] = page_of_blogs.object_list
    context['page_of_blogs'] = page_of_blogs   ###获取最下面<Page 1 of 4>信息，由于博客列表页可以从这里得到，所以与上条信息重复
    context['page_range'] = page_range
    # context['blog_types'] = BlogType.objects.all()
    # context['blog_types'] = blog_types_list
    context['blog_types'] = BlogType.objects.all().annotate(blog_count=Count('blog')) 
    # context['blog_dates'] = Blog.objects.dates('created_time','month',order='DESC')
    context['blog_dates'] = blog_dates_dict
    # context['blogs_count'] = Blog.objects.all().count()  ###另一种统计共有多少篇博客
    return context



def blog_list(request):
    blogs_all_list = Blog.objects.all()   ###获取全部列表
    context = get_blog_list_common_data(request,blogs_all_list)
    return render(request,'blog/blog_list.html',context)



def blogs_with_type(request,blog_type_pk):
    blog_type = get_object_or_404(BlogType,pk=blog_type_pk)
    blogs_all_list = Blog.objects.filter(blog_type=blog_type)   ###获取全部列表
    context = get_blog_list_common_data(request,blogs_all_list)
    context['blog_type'] = blog_type
    return render(request,'blog/blogs_with_type.html',context)



def blogs_with_date(request,year,month):
    blogs_all_list = Blog.objects.filter(created_time__year=year,created_time__month=month)   ###获取全部列表
    context = get_blog_list_common_data(request,blogs_all_list)
    context['blogs_with_date'] = '%s年%s月' % (year,month)
    return render(request,'blog/blogs_with_date.html',context)



def blog_detail(request, blog_pk):
    blog = get_object_or_404(Blog, pk=blog_pk)
    read_cookie_key = read_statistics_once_read(request, blog)

    context = {}
    context['previous_blog'] = Blog.objects.filter(created_time__gt=blog.created_time).last()
    context['next_blog'] = Blog.objects.filter(created_time__lt=blog.created_time).first()
    context['blog'] = blog
    context['login_form'] = LoginForm()
    response = render(request,'blog/blog_detail.html',context)
    # response.set_cookie('blog_%s_readed' % blog_pk,'true')   ###第一个参数是记录主键值；第二参数随便填，标明已读即可；第三个参数,max_age=60是60s记录一次
    response.set_cookie(read_cookie_key,'true') #阅读cookie标记
    return response