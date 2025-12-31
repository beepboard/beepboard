require_relative 'src/app'

run do |env|
    Acrylic::Cascade.serve(env).finish
end
