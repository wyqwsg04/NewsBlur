from pprint import pprint
from django.conf import settings
from apps.reader.models import MUserStory, UserStory
from apps.rss_feeds.models import Feed, Story, MStory, StoryAuthor, Tag
from apps.analyzer.models import MClassifierTitle, MClassifierAuthor, MClassifierFeed, MClassifierTag
from apps.analyzer.models import ClassifierTitle, ClassifierAuthor, ClassifierFeed, ClassifierTag
import mongoengine
import sys
from utils import json

MONGO_DB = settings.MONGO_DB
db = mongoengine.connect(MONGO_DB['NAME'], host=MONGO_DB['HOST'], port=MONGO_DB['PORT'])

def bootstrap_stories():
    print "Mongo DB stories: %s" % MStory.objects().count()
    # db.stories.drop()
    print "Dropped! Mongo DB stories: %s" % MStory.objects().count()

    print "Stories: %s" % Story.objects.all().count()
    pprint(db.stories.index_information())

    feeds = Feed.objects.all().order_by('-average_stories_per_month')
    feed_count = feeds.count()
    i = 0
    for feed in feeds:
        i += 1
        print "%s/%s: %s (%s stories)" % (i, feed_count,
                            feed, Story.objects.filter(story_feed=feed).count())
        sys.stdout.flush()
    
        stories = Story.objects.filter(story_feed=feed).values()
        for story in stories:
            # story['story_tags'] = [tag.name for tag in Tag.objects.filter(story=story['id'])]
            try:
                story['story_tags'] = json.decode(story['story_tags'])
            except:
                continue
            del story['id']
            del story['story_author_id']
            try:
                MStory(**story).save()
            except:
                continue

    print "\nMongo DB stories: %s" % MStory.objects().count()

def bootstrap_userstories():
    print "Mongo DB userstories: %s" % MUserStory.objects().count()
    # db.userstories.drop()
    print "Dropped! Mongo DB userstories: %s" % MUserStory.objects().count()

    print "UserStories: %s" % UserStory.objects.all().count()
    pprint(db.userstories.index_information())

    userstories = UserStory.objects.all().values()
    for userstory in userstories:
        try:
            story = Story.objects.get(pk=userstory['story_id'])
        except Story.DoesNotExist:
            continue
        try:
            userstory['story'] = MStory.objects(story_feed_id=story.story_feed.pk, story_guid=story.story_guid)[0]
        except:
            print '!',
            continue
        print '.',
        del userstory['id']
        del userstory['opinion']
        del userstory['story_id']
        try:
            MUserStory(**userstory).save()
        except:
            print '\n\n!\n\n'
            continue

    print "\nMongo DB userstories: %s" % MUserStory.objects().count()

def bootstrap_classifiers():
    for sql_classifier, mongo_classifier in ((ClassifierTitle, MClassifierTitle), 
                                             (ClassifierAuthor, MClassifierAuthor), 
                                             (ClassifierFeed, MClassifierFeed),
                                             (ClassifierTag, MClassifierTag)):
        collection = mongo_classifier.meta['collection']
        print "Mongo DB classifiers: %s - %s" % (collection, mongo_classifier.objects().count())
        # db[collection].drop()
        print "Dropped! Mongo DB classifiers: %s - %s" % (collection, mongo_classifier.objects().count())

        print "%s: %s" % (sql_classifier._meta.object_name, sql_classifier.objects.all().count())
        pprint(db[collection].index_information())
        
        for userclassifier in sql_classifier.objects.all().values():
            del userclassifier['id']
            if sql_classifier._meta.object_name == 'ClassifierAuthor':
                author = StoryAuthor.objects.get(pk=userclassifier['author_id'])
                userclassifier['author'] = author.author_name
                del userclassifier['author_id']
            if sql_classifier._meta.object_name == 'ClassifierTag':
                tag = Tag.objects.get(pk=userclassifier['tag_id'])
                userclassifier['tag'] = tag.name
                del userclassifier['tag_id']
            print '.',
            try:
                mongo_classifier(**userclassifier).save()
            except:
                print '\n\n!\n\n'
                continue
            
        print "\nMongo DB classifiers: %s - %s" % (collection, mongo_classifier.objects().count())
    
if __name__ == '__main__':
    # bootstrap_stories()
    bootstrap_userstories()
    bootstrap_classifiers()