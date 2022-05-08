# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals

from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.exceptions import IgnoreRequest
from scrapy.spidermiddlewares.offsite import OffsiteMiddleware
from scrapy.utils.response import response_status_message
from twisted.internet import defer, reactor


async def async_sleep(delay, return_value=None):
    deferred = defer.Deferred()
    reactor.callLater(delay, deferred.callback, return_value)
    return await deferred


class TooManyRequestsRetryMiddleware(RetryMiddleware):
    """
    https://stackoverflow.com/a/66131114
    Modifies RetryMiddleware to delay retries on status 429.
    """

    DEFAULT_DELAY = 60
    MAX_DELAY = 600

    async def process_response(self, request, response, spider):
        """
        Like RetryMiddleware.process_response, but, if response status is 429,
        retry the request only after waiting at most self.MAX_DELAY seconds.
        Respect the Retry-After header if it's less than self.MAX_DELAY.
        If Retry-After is absent/invalid, wait only self.DEFAULT_DELAY seconds.
        """

        if request.meta.get('dont_retry', False):
            return response

        if response.status in self.retry_http_codes:
            if response.status == 429:
                retry_after = response.headers.get('retry-after')
                try:
                    retry_after = int(retry_after)
                except (ValueError, TypeError):
                    delay = self.DEFAULT_DELAY
                else:
                    delay = min(self.MAX_DELAY, retry_after)
                spider.logger.warning(f'Retrying {request} in {delay} seconds.')

                spider.crawler.engine.pause()
                await async_sleep(delay)
                spider.crawler.engine.unpause()

            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response

        return response


class StrictOffsiteMiddleware(object):
    """
    Ignore redirects to offsite domains.
    See https://github.com/scrapy/scrapy/issues/2241 for details.
    """

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        filtered_requests = [x for x in self.strict_offsite(request, spider)]
        if len(filtered_requests) == 0:
            spider.logger.warning('Filtered offsite request by strict_offsite to %(request)s', {'request': request})
            raise IgnoreRequest('Forbidden by strict_offsite middleware')
        return None

    def strict_offsite(self, request, spider):
        # here we have only 1 request and we fabricate a "result" array,
        # so we can reuse OffsiteMiddleware here.
        # returns 1 request if not filtered and 0 requests if filtered
        result = [request]
        return self.offsiteMiddleware.process_spider_output('unused_response_arg', result, spider)

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
        self.offsiteMiddleware = OffsiteMiddleware(spider.crawler.stats)
        self.offsiteMiddleware.spider_opened(spider)
