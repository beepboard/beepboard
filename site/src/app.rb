require 'acrylic'
require 'sequel'

DB = Sequel.connect 'sqlite://data/beepboard.db'

require_relative 'songs_n_links'

route path: '/api/v1/**', verb: [:GET, :POST, :PUT, :DELETE, :PATCH] do |conf, req|
    Rack::Response.new "The (undocumented) v1 API is not supported anymore. Please use the v2 API instead.", 410
end

route path: '/api/v2/Shorten', verb: :POST do |conf, req, id|
    
end

route path: '/api/v2/User/<id>', verb: :GET do |conf, req, id|
    
end
