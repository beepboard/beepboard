class User < Sequel::Model
    one_to_many :tokens
end

class Link < Sequel::Model
end

class Tokens < Sequel::Model
    one_to_one :user
end
